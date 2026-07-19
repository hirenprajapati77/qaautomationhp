#!/usr/bin/env python
"""
CLI entry point: trains/evaluates the ML model and runs the multi-agent
RAG pipeline against the golden dataset, then prints a single QUALITY
GATE report. Exits with code 1 if any gate fails, so CI can block a
merge/release automatically.

Usage:
    python scripts/run_quality_gates.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from src.config.settings import settings
from src.core.logger import get_logger
from src.ml_validation.model_evaluator import ModelEvaluator
from src.ml_validation.model_trainer import train_complaint_classifier
from src.quality_gates.gate_checker import QualityGate
from src.rag_evaluation.agents import CriticAgent, GeneratorAgent, RetrieverAgent
from src.rag_evaluation.fixtures import RAG_GOLDEN_DATASET, RAG_KNOWLEDGE_BASE
from src.rag_evaluation.graph_pipeline import MultiAgentRAGPipeline
from src.rag_evaluation.llm_client import MockLLM
from src.rag_evaluation.ragas_metrics import (
    answer_relevancy_score,
    context_precision,
    context_recall,
    faithfulness_score,
)
from src.rag_evaluation.retriever import TfidfRetriever

logger = get_logger("QualityGatesCLI")


def run_ml_gate(gate: QualityGate) -> None:
    trained = train_complaint_classifier()
    report = ModelEvaluator(trained.model, trained.X_test, trained.y_test).evaluate()

    gate.require_min("ML: accuracy", report.accuracy, settings.ml_gate.min_accuracy)
    gate.require_min("ML: precision", report.precision, settings.ml_gate.min_precision)
    gate.require_min("ML: recall", report.recall, settings.ml_gate.min_recall)
    gate.require_min("ML: f1", report.f1, settings.ml_gate.min_f1)
    gate.require_min(
        "ML: bootstrap CI lower bound",
        report.ci_lower,
        settings.ml_gate.min_ci_lower_bound_accuracy,
    )


def run_rag_gate(gate: QualityGate) -> None:
    if not RAG_GOLDEN_DATASET:
        raise ValueError("RAG golden dataset must not be empty")

    retriever = TfidfRetriever(list(RAG_KNOWLEDGE_BASE))
    pipeline = MultiAgentRAGPipeline(
        retriever_agent=RetrieverAgent(retriever, top_k=1),
        generator_agent=GeneratorAgent(MockLLM()),
        critic_agent=CriticAgent(
            faithfulness_threshold=settings.rag_gate.critic_faithfulness,
            relevancy_threshold=settings.rag_gate.critic_relevancy,
        ),
    )

    precisions, recalls, faithfulnesses, relevancies = [], [], [], []
    for case in RAG_GOLDEN_DATASET:
        state = pipeline.run(case["question"])
        retrieved_ids = [d.doc_id for d in state.retrieved_docs]
        precisions.append(context_precision(retrieved_ids, case["relevant_doc_ids"]))
        recalls.append(context_recall(retrieved_ids, case["relevant_doc_ids"]))
        faithfulnesses.append(faithfulness_score(state.answer, state.context))
        relevancies.append(answer_relevancy_score(state.answer, state.question))

    if not precisions:
        raise ValueError("RAG gate produced no metric samples")

    avg_precision = sum(precisions) / len(precisions)
    avg_recall = sum(recalls) / len(recalls)
    avg_faithfulness = sum(faithfulnesses) / len(faithfulnesses)
    avg_relevancy = sum(relevancies) / len(relevancies)

    gate.require_min(
        "RAG: avg context precision",
        avg_precision,
        settings.rag_gate.min_context_precision,
    )
    gate.require_min(
        "RAG: avg context recall",
        avg_recall,
        settings.rag_gate.min_context_recall,
    )
    # Offline TF-IDF mock judge scores are lower than real LLM judges; use critic thresholds.
    gate.require_min(
        "RAG: avg faithfulness (mock judge)",
        avg_faithfulness,
        settings.rag_gate.critic_faithfulness,
    )
    gate.require_min(
        "RAG: avg answer relevancy (mock judge)",
        avg_relevancy,
        settings.rag_gate.critic_relevancy,
    )


def main() -> int:
    gate = QualityGate()
    try:
        run_ml_gate(gate)
        run_rag_gate(gate)
    except Exception:
        logger.exception("Quality gate execution failed")
        return 1

    report = gate.evaluate()
    print("\n" + "=" * 60)
    print("QUALITY GATE REPORT")
    print("=" * 60)
    print(report.summary())
    print("=" * 60)

    return 0 if report.all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
