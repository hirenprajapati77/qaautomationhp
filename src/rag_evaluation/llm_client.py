"""
LLM abstraction layer.

Why an interface instead of calling OpenAI/LangChain directly everywhere?
- Tests and CI must run WITHOUT paid API keys -> we ship a deterministic
  MockLLM that behaves realistically for demo/teaching purposes.
- Swapping to a real model (OpenAI, Anthropic, local Ollama, etc. via
  LangChain's `BaseChatModel`) is a one-line change at the call site -
  see `RealLangChainLLM` below for exactly how that plug-in point works.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
import hashlib

from src.core.logger import get_logger

logger = get_logger("LLMClient")


class BaseLLMClient(ABC):
    @abstractmethod
    def generate(self, prompt: str, context: str = "") -> str:
        ...


class MockLLM(BaseLLMClient):
    """
    Deterministic, offline stand-in for a real LLM.

    It "answers" a question by extracting the sentence(s) from the
    supplied context that share the most words with the question -
    enough of a real behaviour to exercise a genuine RAG evaluation
    pipeline (faithfulness / relevancy scoring) without any network
    call or API key.
    """

    def generate(self, prompt: str, context: str = "") -> str:
        if not context.strip():
            return "I don't have enough information in the provided context to answer that."

        question_words = set(w.lower().strip(".,?!") for w in prompt.split())
        sentences = [s.strip() for s in context.split(".") if s.strip()]

        scored = []
        for sentence in sentences:
            sentence_words = set(w.lower().strip(".,?!") for w in sentence.split())
            overlap = len(question_words & sentence_words)
            scored.append((overlap, sentence))

        scored.sort(key=lambda x: x[0], reverse=True)
        best_sentences = [s for score, s in scored[:2] if score > 0]

        if not best_sentences:
            return "Based on the retrieved documents, I could not find a directly relevant answer."

        answer = ". ".join(best_sentences) + "."
        logger.info("MockLLM generated answer (%d chars) for prompt hash %s",
                     len(answer), hashlib.sha1(prompt.encode()).hexdigest()[:8])
        return answer


class RealLangChainLLM(BaseLLMClient):
    """
    Reference implementation showing how a junior would wire in a REAL
    model via LangChain once API keys are available. Not used by default
    tests/CI so the repo stays runnable with zero secrets.

    Usage:
        from langchain_openai import ChatOpenAI
        llm = RealLangChainLLM(ChatOpenAI(model="gpt-4o-mini", temperature=0))
    """

    def __init__(self, langchain_chat_model):
        self._llm = langchain_chat_model

    def generate(self, prompt: str, context: str = "") -> str:
        full_prompt = f"Context:\n{context}\n\nQuestion: {prompt}\nAnswer using only the context above:"
        response = self._llm.invoke(full_prompt)
        return getattr(response, "content", str(response))
