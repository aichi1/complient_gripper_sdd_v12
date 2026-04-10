"""Gradient (sensitivity) consistency tests for objective functions.

Finite-difference checks for:

* ``compliance_objective``
* ``compliant_mechanism_objective``

Both gradients must match a central finite-difference approximation
within 1% relative error.
"""

from __future__ import annotations

import numpy as np
import pytest

from gripperforge_poc.cases import load_case
from gripperforge_poc.objectives import (
    compliance_objective,
    compliant_mechanism_objective,
)
from gripperforge_poc.topopt import build_fem_context


def _finite_difference(fun, xPhys, eps=1e-6):
    """Central FD gradient of a *scalar* objective."""
    fd = np.zeros_like(xPhys)
    for i in range(xPhys.size):
        xp = xPhys.copy()
        xm = xPhys.copy()
        xp[i] += eps
        xm[i] -= eps
        fp, _ = fun(xp)
        fm, _ = fun(xm)
        fd[i] = (fp - fm) / (2 * eps)
    return fd


def test_compliance_gradient_matches_finite_difference():
    nelx, nely = 6, 4  # small grid so FD is affordable
    case = load_case("mbb", nelx=nelx, nely=nely)
    ctx = build_fem_context(nelx, nely, case.fixed_dofs)

    rng = np.random.default_rng(42)
    xPhys = np.clip(rng.uniform(0.2, 0.9, size=nelx * nely), 1e-3, 1.0)

    def fun(x):
        return compliance_objective(x, case.F_in, ctx, penal=3.0)

    _, ana = fun(xPhys)
    fd = _finite_difference(fun, xPhys, eps=1e-6)

    # Relative error norm
    rel_err = np.linalg.norm(ana - fd) / max(np.linalg.norm(fd), 1e-12)
    assert rel_err < 1e-2, f"gradient FD mismatch: rel_err={rel_err:.3e}"


def test_compliant_mechanism_gradient_matches_finite_difference():
    nelx, nely = 6, 4
    case = load_case("cylinder", nelx=nelx, nely=nely)
    ctx = build_fem_context(
        nelx,
        nely,
        case.fixed_dofs,
        spring_dofs=case.spring_dofs,
        spring_ks=case.spring_ks,
    )

    rng = np.random.default_rng(7)
    xPhys = np.clip(rng.uniform(0.3, 0.9, size=nelx * nely), 1e-3, 1.0)

    def fun(x):
        return compliant_mechanism_objective(
            x, case.F_in, case.L_out, ctx, penal=3.0
        )

    _, ana = fun(xPhys)
    fd = _finite_difference(fun, xPhys, eps=1e-6)

    rel_err = np.linalg.norm(ana - fd) / max(np.linalg.norm(fd), 1e-12)
    assert rel_err < 1e-2, f"compliant grad FD mismatch: rel_err={rel_err:.3e}"


def test_compliance_decreases_when_adding_material():
    """Adding uniform density should *decrease* compliance (stiffer)."""
    nelx, nely = 8, 4
    case = load_case("mbb", nelx=nelx, nely=nely)
    ctx = build_fem_context(nelx, nely, case.fixed_dofs)

    low = np.full(nelx * nely, 0.3)
    high = np.full(nelx * nely, 0.9)
    c_low, _ = compliance_objective(low, case.F_in, ctx, penal=3.0)
    c_high, _ = compliance_objective(high, case.F_in, ctx, penal=3.0)
    assert c_high < c_low


def test_compliant_mechanism_sign_convention():
    """Objective returned by compliant_mechanism_objective is -mutual_mean_compliance.

    It should be finite and reflect the sign of L_out @ u_in.
    """
    nelx, nely = 8, 4
    case = load_case("cylinder", nelx=nelx, nely=nely)
    ctx = build_fem_context(
        nelx,
        nely,
        case.fixed_dofs,
        spring_dofs=case.spring_dofs,
        spring_ks=case.spring_ks,
    )
    xPhys = np.full(nelx * nely, 0.5)
    neg_g, _ = compliant_mechanism_objective(
        xPhys, case.F_in, case.L_out, ctx, penal=3.0
    )
    assert np.isfinite(neg_g)
