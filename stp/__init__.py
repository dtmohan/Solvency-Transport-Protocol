"""
STP Governor package (v2.0-RFC).
Ensures state integrity and recursive solvency for non-deterministic engines.
"""

from .governor import STPKernel, SolvencyZone
from .auditor import InternalEarAuditor

__all__ = ["STPKernel", "SolvencyZone", "InternalEarAuditor"]
