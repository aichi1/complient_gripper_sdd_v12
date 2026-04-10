"""SIMP + OC topology optimization core.

Thin, modular re-implementation of Sigmund's 88-line MATLAB code
(Andreassen et al. 2011) with a plug-in objective function.

Module contents kept under ~200 lines as per SKILL.md constraint.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional, Tuple

import numpy as np

from .filters import FilterMatrix, apply_density_filter, apply_sensitivity_filter, build_filter
from .objectives import FEMContext


def element_stiffness_matrix(E: float = 1.0, nu: float = 0.3) -> np.ndarray:
    """Element stiffness matrix for a 4-node plane-stress Q4 unit square.

    Follows Sigmund 88-line code lk() exactly.
    """
    k = np.array(
        [
            1 / 2 - nu / 6,
            1 / 8 + nu / 8,
            -1 / 4 - nu / 12,
            -1 / 8 + 3 * nu / 8,
            -1 / 4 + nu / 12,
            -1 / 8 - nu / 8,
            nu / 6,
            1 / 8 - 3 * nu / 8,
        ]
    )
    ke = E / (1 - nu**2) * np.array(
        [
            [k[0], k[1], k[2], k[3], k[4], k[5], k[6], k[7]],
            [k[1], k[0], k[7], k[6], k[5], k[4], k[3], k[2]],
            [k[2], k[7], k[0], k[5], k[6], k[3], k[4], k[1]],
            [k[3], k[6], k[5], k[0], k[7], k[2], k[1], k[4]],
            [k[4], k[5], k[6], k[7], k[0], k[1], k[2], k[3]],
            [k[5], k[4], k[3], k[2], k[1], k[0], k[7], k[6]],
            [k[6], k[3], k[4], k[1], k[2], k[7], k[0], k[5]],
            [k[7], k[2], k[1], k[4], k[3], k[6], k[5], k[0]],
        ]
    )
    return ke


def build_fem_context(
    nelx: int,
    nely: int,
    fixed_dofs: np.ndarray,
    nu: float = 0.3,
    spring_dofs: np.ndarray | None = None,
    spring_ks: np.ndarray | None = None,
) -> FEMContext:
    """Build the FEM mapping context: edof matrix, K index arrays, free DOFs.

    Parameters
    ----------
    spring_dofs, spring_ks : optional
        DOF indices and stiffness values for diagonal springs
        (used for compliant-mechanism stabilization, Sigmund 1997).
    """
    ke = element_stiffness_matrix(E=1.0, nu=nu)
    ndof = 2 * (nelx + 1) * (nely + 1)

    # Element DOF map: elements indexed as i*nely + j, node n1 top-left
    edofMat = np.zeros((nelx * nely, 8), dtype=np.int64)
    for elx in range(nelx):
        for ely in range(nely):
            el = elx * nely + ely
            n1 = (nely + 1) * elx + ely
            n2 = (nely + 1) * (elx + 1) + ely
            edofMat[el] = np.array(
                [
                    2 * n1,
                    2 * n1 + 1,
                    2 * n2,
                    2 * n2 + 1,
                    2 * n2 + 2,
                    2 * n2 + 3,
                    2 * n1 + 2,
                    2 * n1 + 3,
                ]
            )

    iK = np.kron(edofMat, np.ones((8, 1))).flatten().astype(np.int64)
    jK = np.kron(edofMat, np.ones((1, 8))).flatten().astype(np.int64)

    all_dofs = np.arange(ndof)
    free_dofs = np.setdiff1d(all_dofs, fixed_dofs, assume_unique=False)

    if spring_dofs is None:
        spring_dofs = np.zeros(0, dtype=np.int64)
        spring_ks = np.zeros(0, dtype=np.float64)
    else:
        spring_dofs = np.asarray(spring_dofs, dtype=np.int64)
        spring_ks = np.asarray(spring_ks, dtype=np.float64)

    return FEMContext(
        ke=ke,
        edofMat=edofMat,
        iK=iK,
        jK=jK,
        free_dofs=free_dofs,
        ndof=ndof,
        spring_dofs=spring_dofs,
        spring_ks=spring_ks,
    )


def oc_update(
    x: np.ndarray,
    dc: np.ndarray,
    dv: np.ndarray,
    volfrac: float,
    move: float = 0.2,
) -> np.ndarray:
    """Optimality-criteria update with bisection on Lagrange multiplier.

    Minimizes an objective whose gradient ``dc`` is given, subject to
    ``sum(x) <= volfrac * nele``. Assumes ``dc <= 0`` (stiffer material
    is always better); for maximizing mutual mean compliance ``dc`` may
    have both signs, so we clip the Be base to zero.
    """
    l1, l2 = 1e-9, 1e9
    nele = x.size
    xnew = np.zeros_like(x)
    # Be = -dc / (lmid * dv) should be >= 0. If dc > 0 at some element we
    # want to remove material there -> force Be = 0.
    dv_safe = np.where(dv != 0, dv, 1e-30)
    while (l2 - l1) / (l2 + l1) > 1e-3:
        lmid = 0.5 * (l1 + l2)
        Be = np.maximum(0.0, -dc / (lmid * dv_safe))
        xnew = np.maximum(
            0.0,
            np.maximum(
                x - move,
                np.minimum(1.0, np.minimum(x + move, x * np.sqrt(Be))),
            ),
        )
        if xnew.sum() - volfrac * nele > 0:
            l1 = lmid
        else:
            l2 = lmid
    return xnew


@dataclass
class TopOptResult:
    xPhys: np.ndarray
    history: List[float] = field(default_factory=list)
    iterations: int = 0
    converged: bool = False
    nelx: int = 0
    nely: int = 0
    objective_value: float = 0.0
    change_history: List[float] = field(default_factory=list)


def optimize(
    objective_fn: Callable[[np.ndarray], Tuple[float, np.ndarray]],
    nelx: int,
    nely: int,
    fm: FilterMatrix,
    volfrac: float = 0.4,
    maxloop: int = 200,
    tol: float = 0.01,
    filter_type: str = "density",
    initial_density: Optional[np.ndarray] = None,
) -> TopOptResult:
    """Run the SIMP + OC optimization loop.

    Parameters
    ----------
    objective_fn : callable
        Maps ``xPhys -> (value, dvalue_dxPhys)``. Should always return a
        *minimization* gradient (i.e. for compliant mechanism the caller
        should have already negated the sign).
    nelx, nely : int
    fm : FilterMatrix
    volfrac : float
    maxloop : int
    tol : float
        Stop when ``max |x_new - x| < tol``.
    filter_type : {"density", "sensitivity"}
    initial_density : np.ndarray, optional
    """
    nele = nelx * nely
    if initial_density is None:
        x = np.full(nele, volfrac)
    else:
        x = initial_density.copy()

    if filter_type == "density":
        xPhys = apply_density_filter(x, fm)
    else:
        xPhys = x.copy()

    history: List[float] = []
    change_history: List[float] = []
    change = 1.0
    loop = 0
    converged = False
    dv = np.ones(nele)

    while change > tol and loop < maxloop:
        loop += 1
        value, dc = objective_fn(xPhys)

        if not np.all(np.isfinite(dc)) or not np.isfinite(value):
            raise FloatingPointError(
                f"Non-finite objective at iteration {loop}: value={value}"
            )

        if filter_type == "sensitivity":
            dc = apply_sensitivity_filter(x, dc, fm)
            dv_eff = dv
        else:  # density filter
            dc = (fm.H @ (dc / fm.Hs))
            dv_eff = (fm.H @ (dv / fm.Hs))

        x_new = oc_update(x, dc, dv_eff, volfrac)

        if filter_type == "density":
            xPhys = apply_density_filter(x_new, fm)
        else:
            xPhys = x_new.copy()

        change = float(np.max(np.abs(x_new - x)))
        x = x_new
        history.append(float(value))
        change_history.append(change)

    converged = change <= tol
    return TopOptResult(
        xPhys=xPhys.reshape(nelx, nely),
        history=history,
        change_history=change_history,
        iterations=loop,
        converged=converged,
        nelx=nelx,
        nely=nely,
        objective_value=float(history[-1]) if history else float("nan"),
    )
