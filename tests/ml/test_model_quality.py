"""
ML model validation tests - CV bullet: "Evaluated Logistic Regression ML
model for customer complaints/satisfaction classification and verified
performance within defined confidence intervals".

These tests don't just check the model "runs" - they enforce a quality
gate: if accuracy/precision/recall/F1 or the bootstrap CI lower bound
drop below the agreed thresholds, the build fails.
"""
import pytest

from src.config.settings import settings
from src.ml_validation.model_evaluator import ModelEvaluator


@pytest.mark.ml
@pytest.mark.quality_gate
class TestComplaintClassifierQuality:

    @pytest.fixture(scope="class")
    def evaluation_report(self, trained_complaint_model):
        evaluator = ModelEvaluator(
            trained_complaint_model.model,
            trained_complaint_model.X_test,
            trained_complaint_model.y_test,
        )
        return evaluator.evaluate()

    def test_accuracy_meets_gate(self, evaluation_report):
        assert evaluation_report.accuracy >= settings.ml_gate.min_accuracy

    def test_precision_meets_gate(self, evaluation_report):
        assert evaluation_report.precision >= settings.ml_gate.min_precision

    def test_recall_meets_gate(self, evaluation_report):
        assert evaluation_report.recall >= settings.ml_gate.min_recall

    def test_f1_meets_gate(self, evaluation_report):
        assert evaluation_report.f1 >= settings.ml_gate.min_f1

    def test_confidence_interval_lower_bound(self, evaluation_report):
        """The 95% bootstrap CI lower bound must not fall below the floor -
        this protects against a model that got lucky on one test split."""
        assert evaluation_report.ci_lower >= settings.ml_gate.min_ci_lower_bound_accuracy

    def test_confusion_matrix_shape_is_binary(self, evaluation_report):
        cm = evaluation_report.confusion_matrix
        assert len(cm) == 2 and all(len(row) == 2 for row in cm)
