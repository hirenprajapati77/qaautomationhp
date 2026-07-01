"""
Shared pytest fixtures for the whole suite.
"""
import sys
from pathlib import Path

import pytest

# Make `src` importable when pytest is run from the repo root.
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.api_automation.api_client import APIClient
from src.ml_validation.model_trainer import train_complaint_classifier
from src.rag_evaluation.llm_client import MockLLM
from src.rag_evaluation.retriever import TfidfRetriever, Document
from src.rag_evaluation.agents import RetrieverAgent, GeneratorAgent, CriticAgent
from src.rag_evaluation.graph_pipeline import MultiAgentRAGPipeline


@pytest.fixture(scope="session")
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture(scope="session")
def trained_complaint_model():
    return train_complaint_classifier()


@pytest.fixture(scope="session")
def rag_knowledge_base() -> list[Document]:
    return [
        Document("doc-1", "Playwright is a Python and JavaScript framework for reliable end-to-end browser testing across Chromium, Firefox and WebKit."),
        Document("doc-2", "PyTest is a Python testing framework that supports fixtures, parametrization and plugins for scalable test suites."),
        Document("doc-3", "RAGAS is an evaluation framework for Retrieval Augmented Generation pipelines, scoring faithfulness, answer relevancy, context precision and context recall."),
        Document("doc-4", "LangGraph lets developers orchestrate multi agent workflows as a state graph with nodes, edges and conditional routing."),
        Document("doc-5", "A quality gate is an automated checkpoint in CI/CD that blocks a release when metrics fall below defined thresholds."),
        Document("doc-6", "Logistic Regression is a classification algorithm often used for binary outcomes such as escalate versus resolve."),
    ]


@pytest.fixture(scope="session")
def rag_pipeline(rag_knowledge_base) -> MultiAgentRAGPipeline:
    retriever = TfidfRetriever(rag_knowledge_base)
    return MultiAgentRAGPipeline(
        retriever_agent=RetrieverAgent(retriever, top_k=1),
        generator_agent=GeneratorAgent(MockLLM()),
        critic_agent=CriticAgent(faithfulness_threshold=0.15, relevancy_threshold=0.1),
        max_attempts=2,
    )
