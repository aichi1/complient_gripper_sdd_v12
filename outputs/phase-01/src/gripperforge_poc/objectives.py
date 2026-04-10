"""Objective functions for SIMP topology optimization.

Two objectives are implemented:

* ``compliance_objective`` — minimize strain energy (standard Sigmund 88).
* ``compliant_mechanism_objective`` — **maximize mutual mean compliance**
  ``L_out @ u_in`` for compliant-mechanism design (Sigmund 1997).

Both return ``(value, element_sensitivities)`` with sensitivities with
respect to the **physical density** ``xPhys``. Filters are applied outside
by the optimizer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple

import numpy as np
from scipy.sparse import csc_matrix
from scipy.sparse.linalg import spsolve


@dataclass
class FEMContext:
    """Precomputed FEM mapping arrays.

    Attributes
    ----------
    ke : np.ndarray
        Element stiffness matrix (8x8, single material, E=1).
    edofMat : np.ndarray
        Shape ``(nele, 8)``; degrees of freedom for each element.
    iK, jK : np.ndarray
        Row / column indices of global stiffness matrix (COO flattened).
    free_dofs : np.ndarray
        DOFs that are not fixed.
    ndof : int
        Total number of DOFs.
    spring_dofs : np.ndarray
        DOFs where diagonal spring stiffness is added (compliant-mechanism
        stabilization, Sigmund 1997).
    spring_ks : np.ndarray
        Corresponding spring stiffness values.
    """

    ke: np.ndarray
    edofMat: np.ndarray
    iK: np.ndarray
    jK: np.ndarray
    free_dofs: np.ndarray
    ndof: int
    spring_dofs: np.ndarray = field(default_factory=lambda: np.zeros(0, dtype=np.int64))
    spring_ks: np.ndarray = field(default_factory=lambda: np.zeros(0, dtype=np.float64))


def assemble_K(xPhys: np.ndarray, penal: float, Emin: float, E0: float,
               ctx: FEMContext) -> csc_matrix:
    """Assemble the global stiffness matrix K for given physical density.

    Diagonal springs from ``ctx.spring_dofs`` are added after the element
    assembly.
    """
    scale = Emin + xPhys**penal * (E0 - Emin)
    sK = (ctx.ke.flatten()[np.newaxis].T * scale).flatten(order="F")
    K = csc_matrix(
        (sK, (ctx.iK, ctx.jK)), shape=(ctx.ndof, ctx.ndof)
    )
    # Symmetrize numerically
    K = (K + K.T) / 2.0

    if ctx.spring_dofs.size > 0:
        # Add diagonal spring stiffness
        K = K.tolil()
        for dof, k in zip(ctx.spring_dofs, ctx.spring_ks):
            K[int(dof), int(dof)] += float(k)
        K = K.tocsc()
    return K


def solve_displacement(
    K: csc_matrix, F: np.ndarray, ctx: FEMContext
) -> np.ndarray:
    """Solve K u = F restricted to free DOFs; return full u (zero on fixed)."""
    u = np.zeros(ctx.ndof)
    Kff = K[ctx.free_dofs, :][:, ctx.free_dofs]
    u[ctx.free_dofs] = spsolve(Kff, F[ctx.free_dofs])
    if not np.all(np.isfinite(u)):
        raise ValueError("Linear solve produced non-finite displacements")
    return u


def compliance_objective(
    xPhys: np.ndarray,
    F: np.ndarray,
    ctx: FEMContext,
    penal: float = 3.0,
    Emin: float = 1e-9,
    E0: float = 1.0,
) -> Tuple[float, np.ndarray]:
    """Standard compliance objective and element-wise sensitivity.

    Returns
    -------
    c : float
        Compliance value ``F @ u``.
    dc : np.ndarray
        dC/dxPhys, shape ``(nele,)``. Always negative for stiffer material.
    """
    K = assemble_K(xPhys, penal, Emin, E0, ctx)
    u = solve_displacement(K, F, ctx)

    # Per-element strain energy: (ue^T ke ue)
    ce = (u[ctx.edofMat] @ ctx.ke * u[ctx.edofMat]).sum(axis=1)
    c = float((Emin + xPhys**penal * (E0 - Emin) * ce).sum() * 0.0 + F @ u)
    # Note: compliance is F^T u = sum_e Ee * ce; we compute via F@u for
    # consistency. Both are equivalent in exact arithmetic.

    dc = -penal * (E0 - Emin) * xPhys ** (penal - 1) * ce
    return c, dc


def compliant_mechanism_objective(
    xPhys: np.ndarray,
    F_in: np.ndarray,
    L_out: np.ndarray,
    ctx: FEMContext,
    penal: float = 3.0,
    Emin: float = 1e-9,
    E0: float = 1.0,
) -> Tuple[float, np.ndarray]:
    """Mutual mean compliance objective for compliant-mechanism design.

    The objective ``g = L_out @ u_in`` is **maximized**. To fit into a
    minimization framework, the optimizer should minimize ``-g``; this
    function therefore returns ``(-g, d(-g)/dxPhys)`` so the caller can
    treat it uniformly.

    Parameters
    ----------
    xPhys : np.ndarray
        Physical density field, shape ``(nele,)``.
    F_in : np.ndarray
        Input (real) load vector, shape ``(ndof,)``.
    L_out : np.ndarray
        Dummy unit load at output point in the desired output direction,
        shape ``(ndof,)``.
    ctx : FEMContext
    penal, Emin, E0 : float

    Returns
    -------
    neg_g : float
        ``-(L_out @ u_in)``. Smaller is better for the optimizer.
    dneg_g : np.ndarray
        Sensitivity of ``-g`` w.r.t. ``xPhys``.

    Notes
    -----
    The gradient via adjoint:

    .. math::

        \\frac{\\partial g}{\\partial x_e}
        = -p (E_0 - E_{min}) x_e^{p-1}
          (u_{out})_e^T k_e (u_{in})_e

    hence ``d(-g)/dx = +p (E0 - Emin) x^(p-1) (u_out . ke . u_in)``.
    """
    K = assemble_K(xPhys, penal, Emin, E0, ctx)
    u_in = solve_displacement(K, F_in, ctx)
    u_out = solve_displacement(K, L_out, ctx)

    g = float(L_out @ u_in)  # mutual mean compliance

    # Element-wise mixed term: u_out_e^T ke u_in_e
    mixed = (u_out[ctx.edofMat] @ ctx.ke * u_in[ctx.edofMat]).sum(axis=1)

    # d(-g)/dx = +p (E0 - Emin) x^(p-1) * mixed
    dneg_g = penal * (E0 - Emin) * xPhys ** (penal - 1) * mixed
    return -g, dneg_g
