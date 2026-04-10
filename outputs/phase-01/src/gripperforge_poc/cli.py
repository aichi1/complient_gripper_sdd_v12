"""Command-line interface for GripperForge Phase 1 PoC.

Run a test case through SIMP + OC optimization and save artifacts.

Example
-------
    python -m gripperforge_poc.cli \\
        --case cylinder \\
        --objective compliant_mechanism \\
        --nelx 80 --nely 40 \\
        --volfrac 0.4 --penal 3.0 --rmin 1.5 \\
        --maxloop 200 --output-dir results
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Callable, Tuple

import numpy as np

from .cases import available_cases, load_case
from .filters import build_filter
from .objectives import compliance_objective, compliant_mechanism_objective
from .topopt import build_fem_context, optimize


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="gripperforge-poc",
        description="GripperForge Phase 1 PoC — SIMP + OC topology optimization "
        "with compliant-mechanism objective.",
    )
    p.add_argument(
        "--case",
        required=True,
        choices=available_cases(),
        help="Test case name (mbb = Sigmund benchmark, others are compliant).",
    )
    p.add_argument(
        "--objective",
        choices=["compliance", "compliant_mechanism"],
        default=None,
        help="Override case default objective.",
    )
    p.add_argument("--nelx", type=int, default=None)
    p.add_argument("--nely", type=int, default=None)
    p.add_argument("--volfrac", type=float, default=None)
    p.add_argument("--penal", type=float, default=3.0)
    p.add_argument("--rmin", type=float, default=1.5)
    p.add_argument("--maxloop", type=int, default=200)
    p.add_argument("--filter", choices=["density", "sensitivity"], default="density")
    p.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results"),
        help="Directory to save results (default: ./results).",
    )
    p.add_argument(
        "--no-save",
        action="store_true",
        help="Skip writing artifacts; print summary only.",
    )
    return p


def _build_objective_fn(
    case, objective_kind: str, penal: float, ctx
) -> Callable[[np.ndarray], Tuple[float, np.ndarray]]:
    if objective_kind == "compliance":
        F = case.F_in
        def obj(xPhys: np.ndarray):
            return compliance_objective(xPhys, F, ctx, penal=penal)
        return obj

    if objective_kind == "compliant_mechanism":
        if case.L_out is None:
            raise ValueError(
                f"Case '{case.name}' does not define L_out; cannot use compliant_mechanism"
            )
        F_in, L_out = case.F_in, case.L_out

        def obj(xPhys: np.ndarray):
            return compliant_mechanism_objective(
                xPhys, F_in, L_out, ctx, penal=penal
            )
        return obj

    raise ValueError(f"Unknown objective: {objective_kind}")


def _save_results(
    case_name: str, result, output_dir: Path
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    # .npy
    np.save(output_dir / f"{case_name}_topology.npy", result.xPhys)

    # .csv history
    hist_path = output_dir / f"{case_name}_history.csv"
    with hist_path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["iteration", "objective", "change"])
        for i, (obj, chg) in enumerate(zip(result.history, result.change_history), start=1):
            w.writerow([i, obj, chg])

    # .png density
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(6, 3))
        ax.imshow(-result.xPhys.T, cmap="gray", vmin=-1, vmax=0)
        ax.set_title(f"{case_name}  iter={result.iterations}  obj={result.objective_value:.3e}")
        ax.axis("off")
        fig.tight_layout()
        fig.savefig(output_dir / f"{case_name}_density.png", dpi=150)
        plt.close(fig)
    except Exception as exc:  # pragma: no cover
        print(f"[warn] failed to save PNG: {exc}", file=sys.stderr)


def main(argv=None) -> int:
    args = _parser().parse_args(argv)

    try:
        case = load_case(args.case, nelx=args.nelx, nely=args.nely)
    except KeyError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    objective_kind = args.objective or case.objective_kind
    volfrac = args.volfrac if args.volfrac is not None else case.volfrac

    ctx = build_fem_context(
        case.nelx,
        case.nely,
        case.fixed_dofs,
        spring_dofs=case.spring_dofs,
        spring_ks=case.spring_ks,
    )
    fm = build_filter(case.nelx, case.nely, args.rmin)
    obj_fn = _build_objective_fn(case, objective_kind, args.penal, ctx)

    print(
        f"[info] case={case.name} obj={objective_kind} "
        f"nelx={case.nelx} nely={case.nely} volfrac={volfrac} "
        f"penal={args.penal} rmin={args.rmin} filter={args.filter}"
    )

    try:
        result = optimize(
            objective_fn=obj_fn,
            nelx=case.nelx,
            nely=case.nely,
            fm=fm,
            volfrac=volfrac,
            maxloop=args.maxloop,
            filter_type=args.filter,
        )
    except FloatingPointError as exc:
        print(f"error: numerical divergence: {exc}", file=sys.stderr)
        return 3
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(
        f"[done] iter={result.iterations} converged={result.converged} "
        f"final_obj={result.objective_value:.4e}"
    )
    if not args.no_save:
        _save_results(case.name, result, args.output_dir)
        print(f"[saved] {args.output_dir}/{case.name}_{{density.png,history.csv,topology.npy}}")

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
