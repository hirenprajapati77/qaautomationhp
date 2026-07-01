"""
BaseTest: the OOP backbone every test class can (optionally) inherit from.

This demonstrates the OOP principles called out in the CV:
- Encapsulation: shared setup/teardown and logging hidden behind simple methods.
- Inheritance: API, E2E, ML and RAG base classes extend this.
- Single Responsibility: this class only knows about generic test lifecycle,
  nothing about HTTP, browsers, or models.
"""
from __future__ import annotations
import time
from src.core.logger import get_logger


class BaseTest:
    """Generic parent for all test-support classes in the framework."""

    def __init__(self) -> None:
        self.logger = get_logger(self.__class__.__name__)
        self._start_time: float | None = None

    def start_timer(self) -> None:
        self._start_time = time.perf_counter()

    def stop_timer(self) -> float:
        if self._start_time is None:
            return 0.0
        elapsed = time.perf_counter() - self._start_time
        self.logger.info("Elapsed time: %.3fs", elapsed)
        return elapsed

    def log_step(self, message: str) -> None:
        self.logger.info("STEP: %s", message)

    def log_assertion(self, description: str, passed: bool) -> None:
        status = "PASS" if passed else "FAIL"
        level = self.logger.info if passed else self.logger.error
        level("ASSERT [%s]: %s", status, description)
