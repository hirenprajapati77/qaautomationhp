"""
Shared RAG knowledge base and golden dataset used by tests and quality gates.

Keeping one definition avoids drift between pytest and the CI gate script.
"""
from __future__ import annotations

from src.rag_evaluation.retriever import Document

RAG_KNOWLEDGE_BASE: list[Document] = [
    Document(
        "doc-1",
        "Playwright is a Python and JavaScript framework for reliable end-to-end "
        "browser testing across Chromium, Firefox and WebKit.",
    ),
    Document(
        "doc-2",
        "PyTest is a Python testing framework that supports fixtures, "
        "parametrization and plugins for scalable test suites.",
    ),
    Document(
        "doc-3",
        "RAGAS is an evaluation framework for Retrieval Augmented Generation "
        "pipelines, scoring faithfulness, answer relevancy, context precision "
        "and context recall.",
    ),
    Document(
        "doc-4",
        "LangGraph lets developers orchestrate multi agent workflows as a state "
        "graph with nodes, edges and conditional routing.",
    ),
    Document(
        "doc-5",
        "A quality gate is an automated checkpoint in CI/CD that blocks a release "
        "when metrics fall below defined thresholds.",
    ),
    Document(
        "doc-6",
        "Logistic Regression is a classification algorithm often used for binary "
        "outcomes such as escalate versus resolve.",
    ),
]

RAG_GOLDEN_DATASET: list[dict] = [
    {
        "question": "What is Playwright used for?",
        "relevant_doc_ids": {"doc-1"},
    },
    {
        "question": "What does RAGAS evaluate in a RAG pipeline?",
        "relevant_doc_ids": {"doc-3"},
    },
    {
        "question": "How does LangGraph orchestrate multi agent workflows?",
        "relevant_doc_ids": {"doc-4"},
    },
    {
        "question": "What is a quality gate in CI/CD?",
        "relevant_doc_ids": {"doc-5"},
    },
]
