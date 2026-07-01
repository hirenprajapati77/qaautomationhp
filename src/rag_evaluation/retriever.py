"""
Retriever: TF-IDF based semantic-ish retrieval over an in-memory
knowledge base.

Real production systems (as in the CV: "LangChain + Chroma (retrieval)")
would embed documents with a vector model and store them in Chroma /
FAISS / Pinecone. We use scikit-learn's TF-IDF + cosine similarity here
so retrieval quality can be evaluated deterministically offline - the
evaluation math (precision/recall over retrieved docs) is identical
regardless of which vector store produced the ranking.

Swapping to real Chroma is a drop-in replacement - see the
`ChromaRetriever` stub at the bottom for the integration point.
"""
from __future__ import annotations
from dataclasses import dataclass

from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
from sklearn.metrics.pairwise import cosine_similarity

from src.core.logger import get_logger

logger = get_logger("Retriever")

# A handful of generic verbs that add noise on a *small* demo knowledge
# base (they'd be fine on a large real corpus, where idf naturally
# suppresses them - but with only a few short documents they can
# dominate similarity scores). Extending sklearn's stop-word list here
# is a normal, documented retrieval-tuning step.
_EXTRA_STOP_WORDS = {"used", "use", "often"}
_STOP_WORDS = list(ENGLISH_STOP_WORDS.union(_EXTRA_STOP_WORDS))


@dataclass
class Document:
    doc_id: str
    text: str


class TfidfRetriever:
    def __init__(self, documents: list[Document]):
        self.documents = documents
        self._vectorizer = TfidfVectorizer(
            stop_words=_STOP_WORDS,
            ngram_range=(1, 2),
            sublinear_tf=True,
        )
        self._matrix = self._vectorizer.fit_transform([d.text for d in documents])


    def retrieve(self, query: str, top_k: int = 3) -> list[Document]:
        query_vec = self._vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, self._matrix).flatten()
        ranked_idx = similarities.argsort()[::-1][:top_k]
        results = [self.documents[i] for i in ranked_idx]
        logger.info("Retrieved %d docs for query %r -> %s", len(results), query, [d.doc_id for d in results])
        return results


class ChromaRetriever:
    """
    Reference stub: how retrieval would look with a real vector store.

        from langchain_community.vectorstores import Chroma
        from langchain_community.embeddings import OpenAIEmbeddings

        vectordb = Chroma.from_texts(texts, OpenAIEmbeddings())
        docs = vectordb.similarity_search(query, k=top_k)

    Not used in tests/CI to keep the repo dependency-light and offline.
    """
    pass
