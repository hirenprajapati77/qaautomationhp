#!/usr/bin/env python
"""
CLI entry point: trains/evaluates the ML model and runs the multi-agent
RAG pipeline against the golden dataset, then prints a single QUALITY
GATE report. Exits with code 1 if any gate fails, so CI can block a
merge/release automatically.

Usage:
    python scripts/run_quality_gates.py
"""
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from src.config.settings import settings
from src.ml_validation.model_trainer import train_complaint_classifier
from src.ml_validation.model_evaluator import ModelEvaluator
from src.rag_evaluation.llm_client import MockLLM
from src.rag_evaluation.retriever import TfidfRetriever, Document
from src.rag_evaluation.agents import RetrieverAgent, GeneratorAgent, CriticAgent
from src.rag_evaluation.graph_pipeline import MultiAgentRAGPipeline
from src.rag_evaluation.ragas_metrics import context_precision, context_recall
from src.quality_gates.gate_checker import QualityGate


def run_ml_gate(gate: QualityGate) -> None:
    trained = train_complaint_classifier()
    report = ModelEvaluator(trained.model, trained.X_test, trained.y_test).evaluate()

    gate.require_min("ML: accuracy", report.accuracy, settings.ml_gate.min_accuracy)
    gate.require_min("ML: precision", report.precision, settings.ml_gate.min_precision)
    gate.require_min("ML: recall", report.recall, settings.ml_gate.min_recall)
    gate.require_min("ML: f1", report.f1, settings.ml_gate.min_f1)
    gate.require_min("ML: bootstrap CI lower bound", report.ci_lower, settings.ml_gate.min_ci_lower_bound_accuracy)


def run_rag_gate(gate: QualityGate) -> None:
    knowledge_base = [
        Document("doc-1", "Playwright is a Python and JavaScript framework for reliable end-to-end browser testing."),
        Document("doc-2", "PyTest is a Python testing framework that supports fixtures and parametrization."),
        Document("doc-3", "RAGAS is an evaluation framework for RAG pipelines, scoring faithfulness and relevancy."),
        Document("doc-4", "LangGraph orchestrates multi agent workflows as a state graph with conditional routing."),
        Document("doc-5", "A quality gate is an automated CI/CD checkpoint that blocks releases below thresholds."),
    ]
    golden_dataset = [
        {"question": "What is Playwright used for?", "relevant_doc_ids": {"doc-1"}},
        {"question": "What does RAGAS evaluate?", "relevant_doc_ids": {"doc-3"}},
        {"question": "What is a quality gate?", "relevant_doc_ids": {"doc-5"}},
    ]

    retriever = TfidfRetriever(knowledge_base)
    pipeline = MultiAgentRAGPipeline(
        retriever_agent=RetrieverAgent(retriever, top_k=1),
        generator_agent=GeneratorAgent(MockLLM()),
        critic_agent=CriticAgent(faithfulness_threshold=0.15, relevancy_threshold=0.1),
    )

    precisions, recalls = [], []
    for case in golden_dataset:
        state = pipeline.run(case["question"])
        retrieved_ids = [d.doc_id for d in state.retrieved_docs]
        precisions.append(context_precision(retrieved_ids, case["relevant_doc_ids"]))
        recalls.append(context_recall(retrieved_ids, case["relevant_doc_ids"]))

    avg_precision = sum(precisions) / len(precisions)
    avg_recall = sum(recalls) / len(recalls)

    gate.require_min("RAG: avg context precision", avg_precision, settings.rag_gate.min_context_precision)
    gate.require_min("RAG: avg context recall", avg_recall, settings.rag_gate.min_context_recall)


def main() -> int:
    gate = QualityGate()
    run_ml_gate(gate)
    run_rag_gate(gate)

    report = gate.evaluate()
    print("\n" + "=" * 60)
    print("QUALITY GATE REPORT")
    print("=" * 60)
    print(report.summary())
    print("=" * 60)

    return 0 if report.all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
