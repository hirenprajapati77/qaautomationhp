"""
ModelEvaluator: computes accuracy / precision / recall / F1 and a
bootstrap confidence interval for accuracy - matching the CV bullet
"verified performance within defined confidence intervals".

This is the reusable evaluation library a QA engineer plugs into ANY
sklearn-compatible classifier, not just the complaint model.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict

import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

from src.core.logger import get_logger

logger = get_logger("ModelEvaluator")


@dataclass
class EvaluationReport:
    accuracy: float
    precision: float
    recall: float
    f1: float
    confusion_matrix: list
    ci_lower: float
    ci_upper: float

    def to_dict(self) -> dict:
        return asdict(self)


class ModelEvaluator:
    def __init__(self, model, X_test: np.ndarray, y_test: np.ndarray):
        self.model = model
        self.X_test = X_test
        self.y_test = y_test
        self.y_pred = model.predict(X_test)

    def bootstrap_accuracy_ci(self, n_bootstrap: int = 1000, ci: float = 0.95, seed: int = 42) -> tuple[float, float]:
        rng = np.random.default_rng(seed)
        n = len(self.y_test)
        accuracies = []

        for _ in range(n_bootstrap):
            idx = rng.integers(0, n, n)
            acc = accuracy_score(self.y_test[idx], self.y_pred[idx])
            accuracies.append(acc)

        alpha = (1 - ci) / 2
        lower = float(np.quantile(accuracies, alpha))
        upper = float(np.quantile(accuracies, 1 - alpha))
        return lower, upper

    def evaluate(self) -> EvaluationReport:
        acc = accuracy_score(self.y_test, self.y_pred)
        prec = precision_score(self.y_test, self.y_pred, zero_division=0)
        rec = recall_score(self.y_test, self.y_pred, zero_division=0)
        f1 = f1_score(self.y_test, self.y_pred, zero_division=0)
        cm = confusion_matrix(self.y_test, self.y_pred).tolist()
        ci_lower, ci_upper = self.bootstrap_accuracy_ci()

        report = EvaluationReport(
            accuracy=round(acc, 4),
            precision=round(prec, 4),
            recall=round(rec, 4),
            f1=round(f1, 4),
            confusion_matrix=cm,
            ci_lower=round(ci_lower, 4),
            ci_upper=round(ci_upper, 4),
        )
        logger.info("Evaluation report: %s", report.to_dict())
        return report
