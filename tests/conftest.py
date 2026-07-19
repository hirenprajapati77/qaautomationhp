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
    import requests
    from urllib.parse import urlparse

    client = APIClient()
    original_request = client.session.request

    def mock_request(method, url, **kwargs):
        parsed = urlparse(url)
        path = parsed.path

        if "reqres.in" in url:
            import datetime
            mock_res = requests.Response()
            mock_res.status_code = 200
            mock_res._content = b"{}"
            mock_res.elapsed = datetime.timedelta(seconds=0.05)

            if method == "GET":
                if path.endswith("/users"):
                    params = kwargs.get("params", {})
                    if params and params.get("page") == 2:
                        mock_res._content = b'{"data": [{"id": 7, "email": "michael.lawson@reqres.in", "first_name": "Michael", "last_name": "Lawson"}]}'
                    else:
                        mock_res._content = b'{"data": [{"id": 1, "email": "george.bluth@reqres.in", "first_name": "George", "last_name": "Bluth"}]}'
                elif path.endswith("/users/2"):
                    mock_res._content = b'{"data": {"id": 2, "email": "janet.weaver@reqres.in", "first_name": "Janet", "last_name": "Weaver"}}'
                elif path.endswith("/users/999"):
                    mock_res.status_code = 404
                    mock_res._content = b"{}"
            elif method == "POST" and path.endswith("/users"):
                mock_res.status_code = 201
                json_data = kwargs.get("json", {})
                name = json_data.get("name", "Unknown")
                mock_res._content = f'{{"name": "{name}", "id": "123", "createdAt": "2026-07-06T19:22:36Z"}}'.encode()
            elif method == "PUT" and path.endswith("/users/2"):
                json_data = kwargs.get("json", {})
                job = json_data.get("job", "Unknown")
                mock_res._content = f'{{"job": "{job}"}}'.encode()
            elif method == "DELETE" and path.endswith("/users/2"):
                mock_res.status_code = 204
                mock_res._content = b""

            return mock_res
        return original_request(method, url, **kwargs)

    client.session.request = mock_request
    return client


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
