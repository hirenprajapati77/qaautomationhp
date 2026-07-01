"""
Trains a Logistic Regression model to classify customer complaints as
"escalate" (1) vs "resolve-in-place" (0) - mirroring the CV bullet:
"Evaluated Logistic Regression ML model for customer complaints/
satisfaction classification".

Uses a synthetic-but-realistic dataset so the whole pipeline runs
offline, deterministically, and in CI with no external data dependency.
"""
from __future__ import annotations
from dataclasses import dataclass

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

from src.core.logger import get_logger

logger = get_logger("ModelTrainer")


@dataclass
class TrainedModel:
    model: LogisticRegression
    X_test: np.ndarray
    y_test: np.ndarray


def _generate_synthetic_complaints(n_samples: int = 2000, seed: int = 42) -> tuple[np.ndarray, np.ndarray]:
    """
    Synthetic features representing a customer-complaint ticket:
      f0 = sentiment_score        (-1 negative ... +1 positive)
      f1 = num_previous_complaints (0..10)
      f2 = response_time_hours    (0..72)
      f3 = account_value_tier     (0..1 normalized)

    Label = 1 (escalate) when sentiment is very negative AND either
    repeat-complaints or slow response time push risk up.
    """
    rng = np.random.default_rng(seed)
    sentiment = rng.uniform(-1, 1, n_samples)
    prior_complaints = rng.integers(0, 11, n_samples)
    response_time = rng.uniform(0, 72, n_samples)
    account_tier = rng.uniform(0, 1, n_samples)

    risk_score = (
        (-sentiment) * 1.8
        + (prior_complaints / 10) * 1.2
        + (response_time / 72) * 1.0
        + account_tier * 0.5
    )
    noise = rng.normal(0, 0.5, n_samples)
    labels = (risk_score + noise > 1.3).astype(int)

    X = np.column_stack([sentiment, prior_complaints, response_time, account_tier])
    return X, labels


def train_complaint_classifier(test_size: float = 0.25, seed: int = 42) -> TrainedModel:
    X, y = _generate_synthetic_complaints(seed=seed)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=seed, stratify=y
    )

    model = LogisticRegression(max_iter=1000, random_state=seed)
    model.fit(X_train, y_train)
    logger.info("Trained LogisticRegression on %d samples (test size=%.0f%%)", len(X_train), test_size * 100)

    return TrainedModel(model=model, X_test=X_test, y_test=y_test)
