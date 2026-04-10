"""Tests for case definitions."""

from __future__ import annotations

import numpy as np
import pytest

from gripperforge_poc.cases import available_cases, load_case


def test_available_cases_nonempty():
    names = available_cases()
    assert len(names) >= 4
    for expected in ("mbb", "cylinder", "box", "lshape"):
        assert expected in names


def test_load_case_unknown_raises():
    with pytest.raises(KeyError):
        load_case("not_a_case")


@pytest.mark.parametrize("name", available_cases())
def test_case_invariants(name):
    case = load_case(name, nelx=20, nely=10)

    # Mesh respected
    assert case.nelx == 20 and case.nely == 10

    ndof = 2 * (case.nelx + 1) * (case.nely + 1)

    # Vectors sized correctly
    assert case.F_in.shape == (ndof,)
    if case.L_out is not None:
        assert case.L_out.shape == (ndof,)

    # fixed_dofs in range and unique
    assert case.fixed_dofs.ndim == 1
    assert case.fixed_dofs.size >= 1
    assert case.fixed_dofs.min() >= 0
    assert case.fixed_dofs.max() < ndof
    assert len(np.unique(case.fixed_dofs)) == case.fixed_dofs.size

    # At least one non-zero entry in F_in
    assert np.count_nonzero(case.F_in) >= 1

    # objective_kind consistent with presence of L_out
    if case.objective_kind == "compliant_mechanism":
        assert case.L_out is not None


def test_mbb_is_compliance_case():
    case = load_case("mbb")
    assert case.objective_kind == "compliance"
    assert case.L_out is None


@pytest.mark.parametrize("name", ["cylinder", "box", "lshape"])
def test_gripper_cases_are_compliant(name):
    case = load_case(name)
    assert case.objective_kind == "compliant_mechanism"
    assert case.L_out is not None
    # L_out should be non-trivial
    assert np.count_nonzero(case.L_out) >= 1
