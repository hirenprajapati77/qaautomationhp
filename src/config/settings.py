"""
Central configuration for the framework.

Design note (for juniors):
------------------------------------------------------------------
All environment-specific values (URLs, timeouts, thresholds) live in
ONE place. Tests and framework code should never hard-code a URL or a
"magic number" threshold - they should import it from here. This is
the same pattern used in real enterprise QA frameworks.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


class ConfigurationError(ValueError):
    """Raised when environment configuration is missing or invalid."""


def _env(key: str, default: str) -> str:
    return os.getenv(key, default)


def _env_int(key: str, default: str) -> int:
    raw = _env(key, default)
    try:
        return int(raw)
    except ValueError as exc:
        raise ConfigurationError(
            f"Environment variable {key}={raw!r} must be an integer"
        ) from exc


def _env_float(key: str, default: str) -> float:
    raw = _env(key, default)
    try:
        return float(raw)
    except ValueError as exc:
        raise ConfigurationError(
            f"Environment variable {key}={raw!r} must be a number"
        ) from exc


def _env_bool(key: str, default: str) -> bool:
    return _env(key, default).strip().lower() in {"1", "true", "yes", "on"}


def _validate_unit_interval(name: str, value: float) -> None:
    if not 0.0 <= value <= 1.0:
        raise ConfigurationError(f"{name} must be between 0 and 1 inclusive, got {value}")


@dataclass(frozen=True)
class APISettings:
    base_url: str = field(default_factory=lambda: _env("API_BASE_URL", "https://reqres.in/api"))
    timeout: int = field(default_factory=lambda: _env_int("API_TIMEOUT", "10"))
    max_retries: int = field(default_factory=lambda: _env_int("API_MAX_RETRIES", "3"))

    def __post_init__(self) -> None:
        if self.timeout <= 0:
            raise ConfigurationError(f"API timeout must be > 0, got {self.timeout}")
        if self.max_retries < 1:
            raise ConfigurationError(f"API max_retries must be >= 1, got {self.max_retries}")
        if not self.base_url.strip():
            raise ConfigurationError("API base_url must not be empty")


@dataclass(frozen=True)
class E2ESettings:
    base_url: str = field(default_factory=lambda: _env("E2E_BASE_URL", "https://the-internet.herokuapp.com"))
    fuzion_base_url: str = field(default_factory=lambda: _env("FUZION_BASE_URL", "https://uat.fuzionhr.com"))
    headless: bool = field(default_factory=lambda: _env_bool("E2E_HEADLESS", "true"))
    default_timeout_ms: int = field(default_factory=lambda: _env_int("E2E_TIMEOUT_MS", "15000"))
    browser: str = field(default_factory=lambda: _env("E2E_BROWSER", "chromium"))

    def __post_init__(self) -> None:
        if self.default_timeout_ms <= 0:
            raise ConfigurationError(
                f"E2E default_timeout_ms must be > 0, got {self.default_timeout_ms}"
            )
        allowed_browsers = {"chromium", "firefox", "webkit"}
        if self.browser not in allowed_browsers:
            raise ConfigurationError(
                f"E2E browser must be one of {sorted(allowed_browsers)}, got {self.browser!r}"
            )


@dataclass(frozen=True)
class MLQualityGate:
    """Minimum acceptable model quality before a release is approved."""
    min_accuracy: float = 0.80
    min_precision: float = 0.75
    min_recall: float = 0.75
    min_f1: float = 0.75
    min_ci_lower_bound_accuracy: float = 0.70  # 95% bootstrap CI lower bound

    def __post_init__(self) -> None:
        for name, value in (
            ("min_accuracy", self.min_accuracy),
            ("min_precision", self.min_precision),
            ("min_recall", self.min_recall),
            ("min_f1", self.min_f1),
            ("min_ci_lower_bound_accuracy", self.min_ci_lower_bound_accuracy),
        ):
            _validate_unit_interval(f"MLQualityGate.{name}", value)


@dataclass(frozen=True)
class RAGQualityGate:
    """Minimum acceptable scores for the agentic RAG pipeline (RAGAS-style)."""
    min_faithfulness: float = 0.75
    min_answer_relevancy: float = 0.70
    min_context_precision: float = 0.70
    min_context_recall: float = 0.70
    # Critic thresholds for the offline TF-IDF mock judge (lower than release gates).
    critic_faithfulness: float = 0.15
    critic_relevancy: float = 0.10

    def __post_init__(self) -> None:
        for name, value in (
            ("min_faithfulness", self.min_faithfulness),
            ("min_answer_relevancy", self.min_answer_relevancy),
            ("min_context_precision", self.min_context_precision),
            ("min_context_recall", self.min_context_recall),
            ("critic_faithfulness", self.critic_faithfulness),
            ("critic_relevancy", self.critic_relevancy),
        ):
            _validate_unit_interval(f"RAGQualityGate.{name}", value)


@dataclass(frozen=True)
class Settings:
    api: APISettings = field(default_factory=APISettings)
    e2e: E2ESettings = field(default_factory=E2ESettings)
    ml_gate: MLQualityGate = field(default_factory=MLQualityGate)
    rag_gate: RAGQualityGate = field(default_factory=RAGQualityGate)


settings = Settings()
