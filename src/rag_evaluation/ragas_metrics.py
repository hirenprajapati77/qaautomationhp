"""
RAGAS-style evaluation metrics, implemented from first principles.

The CV lists "RAGAS" as the evaluation library used in production. Real
RAGAS scores faithfulness/relevancy by asking an LLM-judge (usually
OpenAI) to grade the answer - which requires paid API keys and network
access, so it can't run unattended in this public teaching repo / CI.

Instead we implement the SAME metric definitions using TF-IDF cosine
similarity as a lightweight, deterministic, offline "judge". This keeps
the pipeline 100% free to run while teaching the exact concepts RAGAS
measures:

  * faithfulness        - is the answer grounded in the retrieved context?
                           (does it avoid hallucinating facts not present?)
  * answer_relevancy     - does the answer actually address the question?
  * context_precision    - of the retrieved docs, how many were relevant?
  * context_recall       - of the docs that WERE relevant (golden set),
                           how many did retrieval find?

Swapping in real RAGAS + an LLM judge is a drop-in replacement - see
`real_ragas_evaluate()` at the bottom.
"""
from __future__ import annotations

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def _cosine_sim(text_a: str, text_b: str) -> float:
    if not text_a.strip() or not text_b.strip():
        return 0.0
    vectorizer = TfidfVectorizer(stop_words="english")
    try:
        matrix = vectorizer.fit_transform([text_a, text_b])
    except ValueError:
        # Happens if both texts are pure stopwords / empty after cleaning
        return 0.0
    return float(cosine_similarity(matrix[0:1], matrix[1:2])[0][0])


def faithfulness_score(answer: str, context: str) -> float:
    """How well is the answer grounded in the supplied context?"""
    return round(_cosine_sim(answer, context), 4)


def answer_relevancy_score(answer: str, question: str) -> float:
    """How relevant is the answer to the original question?"""
    return round(_cosine_sim(answer, question), 4)


def context_precision(retrieved_doc_ids: list[str], relevant_doc_ids: set[str]) -> float:
    """Of the docs retrieved, what fraction are actually relevant?"""
    if not retrieved_doc_ids:
        return 0.0
    hits = sum(1 for d in retrieved_doc_ids if d in relevant_doc_ids)
    return round(hits / len(retrieved_doc_ids), 4)


def context_recall(retrieved_doc_ids: list[str], relevant_doc_ids: set[str]) -> float:
    """Of all the docs that SHOULD have been retrieved, how many did we get?"""
    if not relevant_doc_ids:
        return 0.0
    hits = sum(1 for d in relevant_doc_ids if d in retrieved_doc_ids)
    return round(hits / len(relevant_doc_ids), 4)


def real_ragas_evaluate(dataset):
    """
    Reference-only: how this would be scored with the real `ragas`
    library + an LLM judge once an API key is available.

        from ragas import evaluate
        from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
        from datasets import Dataset

        result = evaluate(
            Dataset.from_dict(dataset),
            metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
        )
        return result

    Not used in tests/CI to keep the repo dependency-light and offline.
    """
    raise NotImplementedError("Reference implementation only - see docstring.")
