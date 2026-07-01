"""
Central configuration for the framework.

Design note (for juniors):
------------------------------------------------------------------
All environment-specific values (URLs, timeouts, thresholds) live in
ONE place. Tests and framework code should never hard-code a URL or a
"magic number" threshold - they should import it from here. This is
the same pattern used in real enterprise QA frameworks.
"""
import os
from dataclasses import dataclass, field


def _env(key: str, default: str) -> str:
    return os.getenv(key, default)


@dataclass(frozen=True)
class APISettings:
    base_url: str = _env("API_BASE_URL", "https://reqres.in/api")
    timeout: int = int(_env("API_TIMEOUT", "10"))
    max_retries: int = int(_env("API_MAX_RETRIES", "3"))


@dataclass(frozen=True)
class E2ESettings:
    base_url: str = _env("E2E_BASE_URL", "https://the-internet.herokuapp.com")
    headless: bool = _env("E2E_HEADLESS", "true").lower() == "true"
    default_timeout_ms: int = int(_env("E2E_TIMEOUT_MS", "15000"))
    browser: str = _env("E2E_BROWSER", "chromium")


@dataclass(frozen=True)
class MLQualityGate:
    """Minimum acceptable model quality before a release is approved."""
    min_accuracy: float = 0.80
    min_precision: float = 0.75
    min_recall: float = 0.75
    min_f1: float = 0.75
    min_ci_lower_bound_accuracy: float = 0.70  # 95% bootstrap CI lower bound


@dataclass(frozen=True)
class RAGQualityGate:
    """Minimum acceptable scores for the agentic RAG pipeline (RAGAS-style)."""
    min_faithfulness: float = 0.75
    min_answer_relevancy: float = 0.70
    min_context_precision: float = 0.70
    min_context_recall: float = 0.70


@dataclass(frozen=True)
class Settings:
    api: APISettings = field(default_factory=APISettings)
    e2e: E2ESettings = field(default_factory=E2ESettings)
    ml_gate: MLQualityGate = field(default_factory=MLQualityGate)
    rag_gate: RAGQualityGate = field(default_factory=RAGQualityGate)


settings = Settings()
