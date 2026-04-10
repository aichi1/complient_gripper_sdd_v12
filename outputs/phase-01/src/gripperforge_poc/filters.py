"""Density / sensitivity filters for SIMP topology optimization.

Both filters are implemented via a sparse matrix ``H`` whose entry
``H[i, j] = max(0, r_min - distance(i, j))``. ``Hs[i] = sum_j H[i, j]``.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.sparse import coo_matrix, csr_matrix


@dataclass
class FilterMatrix:
    """Precomputed filter matrix and row sums for a structured grid."""

    H: csr_matrix  # sparse, shape (nele, nele)
    Hs: np.ndarray  # shape (nele,)
    rmin: float
    nelx: int
    nely: int


def build_filter(nelx: int, nely: int, rmin: float) -> FilterMatrix:
    """Build the distance-based filter matrix for an ``nelx x nely`` grid.

    The element indexing matches ``topopt.element_index(x, y) = x * nely + y``
    (x is the column index, y the row index, both zero-based).
    """
    if rmin <= 0:
        raise ValueError("rmin must be positive")

    nele = nelx * nely
    # Estimate max neighbours to preallocate COO buffers
    r = int(np.ceil(rmin))
    max_nbr = (2 * r + 1) ** 2
    iH = np.zeros(nele * max_nbr, dtype=np.int64)
    jH = np.zeros(nele * max_nbr, dtype=np.int64)
    sH = np.zeros(nele * max_nbr, dtype=np.float64)

    cc = 0
    for i in range(nelx):
        for j in range(nely):
            e1 = i * nely + j
            for k in range(max(i - r, 0), min(i + r + 1, nelx)):
                for l in range(max(j - r, 0), min(j + r + 1, nely)):
                    e2 = k * nely + l
                    fac = rmin - np.sqrt((i - k) ** 2 + (j - l) ** 2)
                    if fac > 0:
                        iH[cc] = e1
                        jH[cc] = e2
                        sH[cc] = fac
                        cc += 1

    H = coo_matrix(
        (sH[:cc], (iH[:cc], jH[:cc])), shape=(nele, nele)
    ).tocsr()
    Hs = np.asarray(H.sum(axis=1)).ravel()
    return FilterMatrix(H=H, Hs=Hs, rmin=rmin, nelx=nelx, nely=nely)


def apply_density_filter(x: np.ndarray, fm: FilterMatrix) -> np.ndarray:
    """Physical density ``xPhys`` from design variable ``x`` (density filter)."""
    return (fm.H @ x) / fm.Hs


def apply_sensitivity_filter(
    x: np.ndarray, dc: np.ndarray, fm: FilterMatrix
) -> np.ndarray:
    """Sensitivity filter (Sigmund 1997).

    Parameters
    ----------
    x : np.ndarray
        Current design variables (shape ``(nele,)``). Used as weights.
    dc : np.ndarray
        Un-filtered sensitivities to be smoothed.
    fm : FilterMatrix
    """
    # Avoid division by zero at empty elements
    x_safe = np.maximum(x, 1e-3)
    numer = fm.H @ (x * dc)
    return numer / (x_safe * fm.Hs)
