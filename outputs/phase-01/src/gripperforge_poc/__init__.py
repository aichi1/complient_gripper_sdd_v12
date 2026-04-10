"""GripperForge Phase 1 PoC.

Python re-implementation of Sigmund's 88-line topology optimization,
extended with a compliant-mechanism objective (mutual mean compliance).
"""

from .topopt import TopOptResult, optimize
from .objectives import (
    compliance_objective,
    compliant_mechanism_objective,
)
from .cases import Case, available_cases, load_case

__all__ = [
    "TopOptResult",
    "optimize",
    "compliance_objective",
    "compliant_mechanism_objective",
    "Case",
    "available_cases",
    "load_case",
]

__version__ = "0.1.0"
