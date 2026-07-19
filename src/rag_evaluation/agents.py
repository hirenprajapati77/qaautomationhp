"""
Multi-Agent RAG system.

Mirrors the CV bullet: "Built and evaluated Multi Agent RAG system and a
multiagent evaluation pipeline". Three cooperating agents, each with a
single responsibility (classic multi-agent design):

  1. RetrieverAgent - fetches candidate context from the knowledge base.
  2. GeneratorAgent  - drafts an answer strictly from that context.
  3. CriticAgent      - reviews the draft for faithfulness/relevancy and
                         either approves it or asks the Generator to retry.

The CriticAgent's approve/reject loop is what makes this "agentic"
rather than a single linear RAG call - it is orchestrated as a graph
in graph_pipeline.py (LangGraph-style state machine).
"""
from __future__ import annotations
from dataclasses import dataclass, field

from src.rag_evaluation.llm_client import BaseLLMClient
from src.rag_evaluation.retriever import TfidfRetriever, Document
from src.rag_evaluation.ragas_metrics import faithfulness_score, answer_relevancy_score
from src.core.logger import get_logger

logger = get_logger("Agents")


@dataclass
class AgentState:
    """Shared state object passed between agents in the graph, exactly
    like LangGraph's `StateGraph` shared-state pattern."""
    question: str
    retrieved_docs: list[Document] = field(default_factory=list)
    context: str = ""
    answer: str = ""
    faithfulness: float = 0.0
    relevancy: float = 0.0
    attempts: int = 0
    approved: bool = False
    trace: list[str] = field(default_factory=list)


class RetrieverAgent:
    def __init__(self, retriever: TfidfRetriever, top_k: int = 3):
        self.retriever = retriever
        self.top_k = top_k

    def run(self, state: AgentState) -> AgentState:
        docs = self.retriever.retrieve(state.question, top_k=self.top_k)
        state.retrieved_docs = docs
        state.context = " ".join(d.text for d in docs)
        state.trace.append(f"RetrieverAgent: fetched {len(docs)} docs")
        return state


class GeneratorAgent:
    def __init__(self, llm: BaseLLMClient):
        self.llm = llm

    def run(self, state: AgentState) -> AgentState:
        state.attempts += 1
        state.answer = self.llm.generate(state.question, state.context)
        state.trace.append(f"GeneratorAgent: drafted answer (attempt {state.attempts})")
        return state


class CriticAgent:
    """Scores the draft answer and decides whether it clears the bar."""

    def __init__(self, faithfulness_threshold: float = 0.5, relevancy_threshold: float = 0.4):
        for name, value in (
            ("faithfulness_threshold", faithfulness_threshold),
            ("relevancy_threshold", relevancy_threshold),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1 inclusive, got {value}")
        self.faithfulness_threshold = faithfulness_threshold
        self.relevancy_threshold = relevancy_threshold

    def run(self, state: AgentState) -> AgentState:
        state.faithfulness = faithfulness_score(state.answer, state.context)
        state.relevancy = answer_relevancy_score(state.answer, state.question)

        state.approved = (
            state.faithfulness >= self.faithfulness_threshold
            and state.relevancy >= self.relevancy_threshold
        )
        state.trace.append(
            f"CriticAgent: faithfulness={state.faithfulness:.2f}, "
            f"relevancy={state.relevancy:.2f}, approved={state.approved}"
        )
        logger.info(state.trace[-1])
        return state
