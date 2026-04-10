"""Test case definitions for Phase 1 PoC.

Each case builds a ``Case`` namedtuple with:

* ``nelx``, ``nely`` — mesh dimensions
* ``fixed_dofs`` — DOFs with Dirichlet BC
* ``F_in`` — real load vector (shape ``(ndof,)``)
* ``L_out`` — dummy output load (optional; compliance cases use ``F_in``)
* ``objective_kind`` — ``"compliance"`` or ``"compliant_mechanism"``

Coordinates follow Sigmund's convention: element ``(elx, ely)`` at column
``elx`` and row ``ely`` (top = ``ely=0``). Node DOF index for node
``(nx, ny)`` is ``2*((nely+1)*nx + ny)``.

Cases provided:

* ``mbb`` — Sigmund 88-line benchmark (half MBB beam), *compliance*.
* ``cylinder`` — hollow grip around a Ø30 mm cylinder, *compliant*.
* ``box`` — rectangular (box) workpiece grip, *compliant*.
* ``lshape`` — L-shaped workpiece grip, *compliant*.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Literal, Optional

import numpy as np


ObjectiveKind = Literal["compliance", "compliant_mechanism"]


@dataclass
class Case:
    name: str
    nelx: int
    nely: int
    fixed_dofs: np.ndarray
    F_in: np.ndarray
    L_out: Optional[np.ndarray]
    objective_kind: ObjectiveKind
    description: str
    volfrac: float = 0.4
    # Optional diagonal springs (Sigmund 1997 compliant-mechanism stabilization)
    spring_dofs: Optional[np.ndarray] = None
    spring_ks: Optional[np.ndarray] = None


def _dof(nx: int, ny: int, nely: int, axis: int) -> int:
    """Global DOF index for node (nx, ny), axis = 0 (x) or 1 (y)."""
    return 2 * ((nely + 1) * nx + ny) + axis


def _mbb(nelx: int = 60, nely: int = 20) -> Case:
    ndof = 2 * (nelx + 1) * (nely + 1)
    F = np.zeros(ndof)
    # Unit downward load at top-left corner
    F[_dof(0, 0, nely, 1)] = -1.0
    # Symmetry: left edge fixed in x, single point at bottom-right fixed in y
    fixed = [_dof(0, j, nely, 0) for j in range(nely + 1)]
    fixed.append(_dof(nelx, nely, nely, 1))
    return Case(
        name="mbb",
        nelx=nelx,
        nely=nely,
        fixed_dofs=np.array(fixed, dtype=np.int64),
        F_in=F,
        L_out=None,
        objective_kind="compliance",
        description="Half MBB beam — Sigmund 88-line benchmark for stiffness",
        volfrac=0.5,
    )


def _compliant_cantilever(
    name: str,
    nelx: int,
    nely: int,
    in_y_frac: float,
    out_y_frac: float,
    out_axis: int,
    description: str,
) -> Case:
    """Cantilever-style compliant-mechanism case (Sigmund 1997 style).

    * Entire left edge pinned (both DOFs) → cantilever anchor.
    * Input: unit +x load at right edge, vertical position ``in_y_frac * nely``.
    * Output: desired -1 displacement at right edge, vertical position
      ``out_y_frac * nely``, in direction ``out_axis`` (0 = x, 1 = y).
    * Input / output springs (k = 0.1) added for stabilization.

    This layout gives the design domain a genuine lever arm between input
    and output so that the optimizer can transmit motion through the
    structure.
    """
    ndof = 2 * (nelx + 1) * (nely + 1)
    F_in = np.zeros(ndof)
    L_out = np.zeros(ndof)

    in_y = int(round(in_y_frac * nely))
    out_y = int(round(out_y_frac * nely))

    in_dof = _dof(nelx, in_y, nely, 0)  # +x input at right edge
    out_dof = _dof(nelx, out_y, nely, out_axis)

    F_in[in_dof] = 1.0
    L_out[out_dof] = -1.0  # we want the material to pull this DOF in -direction

    fixed = []
    # Entire left edge pinned
    for ny_ in range(nely + 1):
        fixed.append(_dof(0, ny_, nely, 0))
        fixed.append(_dof(0, ny_, nely, 1))

    spring_dofs = np.array([in_dof, out_dof], dtype=np.int64)
    spring_ks = np.array([0.1, 0.1], dtype=np.float64)

    return Case(
        name=name,
        nelx=nelx,
        nely=nely,
        fixed_dofs=np.unique(np.array(fixed, dtype=np.int64)),
        F_in=F_in,
        L_out=L_out,
        objective_kind="compliant_mechanism",
        description=description,
        volfrac=0.4,
        spring_dofs=spring_dofs,
        spring_ks=spring_ks,
    )


def _cylinder(nelx: int = 80, nely: int = 40) -> Case:
    # Input at upper-right, output at lower-right in -x direction
    return _compliant_cantilever(
        name="cylinder",
        nelx=nelx,
        nely=nely,
        in_y_frac=0.25,
        out_y_frac=0.75,
        out_axis=0,
        description="Compliant gripper for Ø30 mm cylindrical workpiece",
    )


def _box(nelx: int = 80, nely: int = 40) -> Case:
    # Same cantilever shape but different input/output spacing
    return _compliant_cantilever(
        name="box",
        nelx=nelx,
        nely=nely,
        in_y_frac=0.1,
        out_y_frac=0.9,
        out_axis=0,
        description="Compliant gripper for rectangular box workpiece",
    )


def _lshape(nelx: int = 80, nely: int = 40) -> Case:
    """L-shaped compliant case with -y output direction.

    For PoC simplicity we keep the rectangular design domain (the L shape
    will come from the optimization removing material in the unused
    quadrant). The output axis is vertical (-y) to distinguish this case
    from ``cylinder`` / ``box`` which use horizontal output.
    """
    return _compliant_cantilever(
        name="lshape",
        nelx=nelx,
        nely=nely,
        in_y_frac=0.5,
        out_y_frac=0.1,
        out_axis=0,
        description="Compliant gripper for L-shaped workpiece",
    )


_REGISTRY: Dict[str, "callable"] = {
    "mbb": _mbb,
    "cylinder": _cylinder,
    "box": _box,
    "lshape": _lshape,
}


def available_cases() -> list[str]:
    """Return the sorted list of available case names."""
    return sorted(_REGISTRY.keys())


def load_case(name: str, nelx: Optional[int] = None, nely: Optional[int] = None) -> Case:
    """Load a case by name; optionally override mesh size."""
    if name not in _REGISTRY:
        raise KeyError(
            f"Unknown case '{name}'. Available: {', '.join(available_cases())}"
        )
    factory = _REGISTRY[name]
    kwargs = {}
    if nelx is not None:
        kwargs["nelx"] = nelx
    if nely is not None:
        kwargs["nely"] = nely
    return factory(**kwargs)
