"""
Shared pytest fixtures for the whole suite.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.parse import urlparse

import pytest
import requests

# Make `src` importable when pytest is run from the repo root.
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.api_automation.api_client import APIClient
from src.config.settings import settings
from src.ml_validation.model_trainer import train_complaint_classifier
from src.rag_evaluation.agents import CriticAgent, GeneratorAgent, RetrieverAgent
from src.rag_evaluation.fixtures import RAG_KNOWLEDGE_BASE
from src.rag_evaluation.graph_pipeline import MultiAgentRAGPipeline
from src.rag_evaluation.llm_client import MockLLM
from src.rag_evaluation.retriever import Document, TfidfRetriever


@pytest.fixture(scope="session")
def api_client():
    """Session-scoped mocked API client bound to settings.api.base_url."""
    client = APIClient()
    original_request = client.session.request
    base_host = urlparse(client.base_url).netloc

    def mock_request(method, url, **kwargs):
        parsed = urlparse(url)
        path = parsed.path
        host = parsed.netloc

        # Only stub the configured API host so a custom base URL cannot
        # accidentally hit the live network during unit tests.
        if host == base_host or base_host in url:
            import datetime

            mock_res = requests.Response()
            mock_res.status_code = 200
            mock_res._content = b"{}"
            mock_res.elapsed = datetime.timedelta(seconds=0.05)
            mock_res.url = url

            if method == "GET":
                if path.endswith("/users"):
                    params = kwargs.get("params") or {}
                    if params.get("page") == 2:
                        mock_res._content = json.dumps(
                            {
                                "data": [
                                    {
                                        "id": 7,
                                        "email": "michael.lawson@reqres.in",
                                        "first_name": "Michael",
                                        "last_name": "Lawson",
                                    }
                                ]
                            }
                        ).encode()
                    else:
                        mock_res._content = json.dumps(
                            {
                                "data": [
                                    {
                                        "id": 1,
                                        "email": "george.bluth@reqres.in",
                                        "first_name": "George",
                                        "last_name": "Bluth",
                                    }
                                ]
                            }
                        ).encode()
                elif path.endswith("/users/2"):
                    mock_res._content = json.dumps(
                        {
                            "data": {
                                "id": 2,
                                "email": "janet.weaver@reqres.in",
                                "first_name": "Janet",
                                "last_name": "Weaver",
                            }
                        }
                    ).encode()
                elif path.endswith("/users/999"):
                    mock_res.status_code = 404
                    mock_res._content = b"{}"
            elif method == "POST" and path.endswith("/users"):
                mock_res.status_code = 201
                json_data = kwargs.get("json") or {}
                mock_res._content = json.dumps(
                    {
                        "name": json_data.get("name", "Unknown"),
                        "id": "123",
                        "createdAt": "2026-07-06T19:22:36Z",
                    }
                ).encode()
            elif method == "PUT" and path.endswith("/users/2"):
                json_data = kwargs.get("json") or {}
                mock_res._content = json.dumps(
                    {"job": json_data.get("job", "Unknown")}
                ).encode()
            elif method == "DELETE" and path.endswith("/users/2"):
                mock_res.status_code = 204
                mock_res._content = b""

            return mock_res
        return original_request(method, url, **kwargs)

    client.session.request = mock_request
    try:
        yield client
    finally:
        client.close()


@pytest.fixture(scope="session")
def trained_complaint_model():
    return train_complaint_classifier()


@pytest.fixture(scope="session")
def rag_knowledge_base() -> list[Document]:
    return list(RAG_KNOWLEDGE_BASE)


@pytest.fixture(scope="session")
def rag_pipeline(rag_knowledge_base) -> MultiAgentRAGPipeline:
    retriever = TfidfRetriever(rag_knowledge_base)
    return MultiAgentRAGPipeline(
        retriever_agent=RetrieverAgent(retriever, top_k=1),
        generator_agent=GeneratorAgent(MockLLM()),
        critic_agent=CriticAgent(
            faithfulness_threshold=settings.rag_gate.critic_faithfulness,
            relevancy_threshold=settings.rag_gate.critic_relevancy,
        ),
        max_attempts=2,
    )
