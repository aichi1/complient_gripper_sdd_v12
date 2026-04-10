"""Tests for topopt.py — SIMP + OC core."""

from __future__ import annotations

import numpy as np
import pytest

from gripperforge_poc.cases import load_case
from gripperforge_poc.filters import build_filter
from gripperforge_poc.objectives import compliance_objective, assemble_K
from gripperforge_poc.topopt import (
    build_fem_context,
    element_stiffness_matrix,
    oc_update,
    optimize,
)


def test_element_stiffness_matrix_shape_and_symmetry():
    ke = element_stiffness_matrix(E=1.0, nu=0.3)
    assert ke.shape == (8, 8)
    assert np.allclose(ke, ke.T, atol=1e-12)
    # Rigid-body modes: sum of each row should be zero (no external force)
    assert np.allclose(ke.sum(axis=0), 0.0, atol=1e-10)


def test_fem_context_dof_counts_are_consistent():
    nelx, nely = 10, 5
    case = load_case("mbb", nelx=nelx, nely=nely)
    ctx = build_fem_context(nelx, nely, case.fixed_dofs)
    assert ctx.ndof == 2 * (nelx + 1) * (nely + 1)
    # free + fixed should cover all DOFs exactly
    fixed_set = set(case.fixed_dofs.tolist())
    free_set = set(ctx.free_dofs.tolist())
    assert fixed_set.isdisjoint(free_set)
    assert fixed_set | free_set == set(range(ctx.ndof))


def test_oc_update_respects_volume_constraint():
    nele = 20
    x = np.full(nele, 0.5)
    dc = -np.ones(nele)  # uniform gradient
    dv = np.ones(nele)
    xnew = oc_update(x, dc, dv, volfrac=0.4)
    assert xnew.min() >= 0.0 and xnew.max() <= 1.0
    # Volume constraint is satisfied (approximately, from bisection tolerance)
    assert xnew.sum() == pytest.approx(0.4 * nele, rel=5e-3)


def test_oc_update_handles_positive_gradient():
    """If dc > 0 everywhere, the optimizer should remove material uniformly."""
    nele = 20
    x = np.full(nele, 0.5)
    dc = np.ones(nele)  # want to remove material
    dv = np.ones(nele)
    xnew = oc_update(x, dc, dv, volfrac=0.4)
    assert xnew.min() >= 0.0
    # All moves are downward, so mean density must drop or equal 0.5 - move
    assert xnew.mean() <= 0.5


def test_mbb_case_converges_and_reduces_compliance():
    """Regression: Sigmund 88-line MBB should reduce compliance."""
    nelx, nely = 30, 10
    case = load_case("mbb", nelx=nelx, nely=nely)
    ctx = build_fem_context(nelx, nely, case.fixed_dofs)
    fm = build_filter(nelx, nely, rmin=1.5)

    def obj(xPhys: np.ndarray):
        return compliance_objective(xPhys, case.F_in, ctx, penal=3.0)

    result = optimize(
        obj,
        nelx,
        nely,
        fm,
        volfrac=0.5,
        maxloop=30,
        filter_type="density",
    )

    assert result.iterations >= 1
    assert result.xPhys.shape == (nelx, nely)
    # Compliance should be *lower* at the end than at the first iteration.
    assert result.history[-1] < result.history[0]
    # And never NaN / Inf
    assert np.all(np.isfinite(result.history))


def test_mbb_case_symmetry_no_crash_with_small_grid():
    """Tiny grid sanity check: run the full pipeline, assert no exceptions."""
    nelx, nely = 12, 6
    case = load_case("mbb", nelx=nelx, nely=nely)
    ctx = build_fem_context(nelx, nely, case.fixed_dofs)
    fm = build_filter(nelx, nely, rmin=1.5)

    def obj(xPhys):
        return compliance_objective(xPhys, case.F_in, ctx, penal=3.0)

    result = optimize(obj, nelx, nely, fm, volfrac=0.5, maxloop=15)
    assert result.xPhys.shape == (nelx, nely)
    assert np.all(np.isfinite(result.xPhys))
    # OC should always return feasible densities
    assert result.xPhys.min() >= 0.0 - 1e-12
    assert result.xPhys.max() <= 1.0 + 1e-12
