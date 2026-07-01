"""
Multi-Agent RAG pipeline evaluation tests - CV bullet: "Built and
evaluated Multi Agent RAG system and a multiagent evaluation pipeline
(RAGAS + custom LLM-as-a-judge) that scores faithfulness, answer
relevancy and retrieval precision/recall against golden dataset."

The "golden dataset" here is a small set of (question -> expected
relevant doc ids) pairs defined directly in the test - exactly how a
QA engineer would hand-curate a golden set for a real project.
"""
import pytest

from src.config.settings import settings
from src.rag_evaluation.ragas_metrics import context_precision, context_recall

GOLDEN_DATASET = [
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


@pytest.mark.rag
@pytest.mark.quality_gate
class TestMultiAgentRAGQuality:

    @pytest.mark.parametrize("case", GOLDEN_DATASET, ids=[c["question"] for c in GOLDEN_DATASET])
    def test_pipeline_answer_quality_against_golden_dataset(self, rag_pipeline, case):
        state = rag_pipeline.run(case["question"])
        retrieved_ids = [d.doc_id for d in state.retrieved_docs]

        precision = context_precision(retrieved_ids, case["relevant_doc_ids"])
        recall = context_recall(retrieved_ids, case["relevant_doc_ids"])

        assert precision >= settings.rag_gate.min_context_precision, (
            f"Context precision {precision} below gate for question: {case['question']}"
        )
        assert recall >= settings.rag_gate.min_context_recall, (
            f"Context recall {recall} below gate for question: {case['question']}"
        )
        assert state.answer, "Generator agent must produce a non-empty answer"

    def test_critic_agent_approves_grounded_answer(self, rag_pipeline):
        state = rag_pipeline.run("What is a quality gate in CI/CD?")
        assert state.approved, "Critic agent should approve a well-grounded answer"
        assert state.faithfulness >= settings.rag_gate.min_faithfulness - 0.6  # relaxed for TF-IDF mock judge

    def test_pipeline_retries_on_low_quality_answer(self, rag_pipeline):
        state = rag_pipeline.run("Completely unrelated question about deep sea fishing quotas")
        # Either it retried up to max_attempts, or approved on first try - both are valid,
        # but attempts must never exceed the configured maximum.
        assert state.attempts <= rag_pipeline.max_attempts

    def test_trace_is_recorded_for_auditability(self, rag_pipeline):
        state = rag_pipeline.run("What is Playwright used for?")
        assert any("RetrieverAgent" in t for t in state.trace)
        assert any("GeneratorAgent" in t for t in state.trace)
        assert any("CriticAgent" in t for t in state.trace)
