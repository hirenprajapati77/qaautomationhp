"""
QualityGate: the "should this release ship?" decision layer.

This is the piece that turns raw metrics (from ML evaluation, RAG
evaluation, or any other suite) into a single PASS/FAIL release
decision - the automatable equivalent of a QA sign-off. CI calls
`scripts/run_quality_gates.py`, which uses this class, and fails the
build (non-zero exit code) if any gate is not met.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from src.core.logger import get_logger

logger = get_logger("QualityGate")


@dataclass
class GateResult:
    name: str
    passed: bool
    actual: float
    threshold: float
    comparison: str  # ">=" or "<="

    def __str__(self) -> str:
        symbol = "PASS" if self.passed else "FAIL"
        return (
            f"[{symbol}] {self.name}: actual={self.actual:.4f} "
            f"{self.comparison} threshold={self.threshold:.4f}"
        )


@dataclass
class QualityGateReport:
    results: list[GateResult] = field(default_factory=list)

    @property
    def all_passed(self) -> bool:
        # Fail closed: an empty gate report must not silently pass.
        if not self.results:
            return False
        return all(r.passed for r in self.results)

    def summary(self) -> str:
        if not self.results:
            return "No quality checks were registered.\n\nOVERALL: FAIL ❌"
        lines = [str(r) for r in self.results]
        lines.append(f"\nOVERALL: {'PASS ✅' if self.all_passed else 'FAIL ❌'}")
        return "\n".join(lines)


class QualityGate:
    """Evaluate a dict of metric_name -> actual_value against thresholds."""

    def __init__(self):
        self._checks: list[GateResult] = []

    def require_min(self, name: str, actual: float, threshold: float) -> "QualityGate":
        result = GateResult(name, actual >= threshold, actual, threshold, ">=")
        self._checks.append(result)
        logger.info("%s", result)
        return self

    def require_max(self, name: str, actual: float, threshold: float) -> "QualityGate":
        result = GateResult(name, actual <= threshold, actual, threshold, "<=")
        self._checks.append(result)
        logger.info("%s", result)
        return self

    def evaluate(self) -> QualityGateReport:
        return QualityGateReport(results=list(self._checks))
