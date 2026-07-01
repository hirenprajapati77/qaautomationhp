# QA Agentic Automation & Evaluation Framework

A hands-on teaching codebase built by a Principal SDET to onboard junior QA/SDET engineers onto **every technology used in production**: API automation, Playwright E2E, Python OOP frameworks, ML model validation, and — the centerpiece — a **Multi-Agent RAG system with an automated evaluation pipeline and CI quality gates**.

Clone it, run it, break it, read the code. Every module has teaching comments explaining *why* it's built the way it is, not just *what* it does.

---

## 1. What you'll learn from this repo

| Area | Technologies | Where |
|---|---|---|
| API Test Automation | `requests`, PyTest, REST assertions | `src/api_automation/`, `tests/api/` |
| E2E Automation | Playwright, Page Object Model | `src/e2e_automation/`, `tests/e2e/` |
| Python OOP Framework Design | Inheritance, encapsulation, SRP | `src/core/` |
| ML Model Validation | scikit-learn, Logistic Regression, confusion matrix, bootstrap confidence intervals | `src/ml_validation/`, `tests/ml/` |
| Multi-Agent RAG System | LangGraph-style orchestration, LangChain-style retrieval, RAGAS-style scoring | `src/rag_evaluation/`, `tests/rag/` |
| Quality Gates & CI/CD | pass/fail release gating, GitHub Actions | `src/quality_gates/`, `scripts/`, `.github/workflows/` |

---

## 2. Why the RAG stack is "offline-safe"

Real production RAG evaluation (as run in industry) uses **RAGAS + an LLM-as-a-judge** (usually OpenAI) and a **real vector store** (Chroma/FAISS). That needs paid API keys and network access — which breaks the whole point of a repo juniors should `git clone` and run immediately, and breaks CI.

So this repo re-implements the **same evaluation math** (faithfulness, answer relevancy, context precision/recall) using TF-IDF cosine similarity as a deterministic, free, offline judge — and a `MockLLM` that behaves like a real model without calling one. Every file that stubs out a real integration has a docstring showing **exactly** how to swap in the real thing (`RealLangChainLLM`, `ChromaRetriever`, `build_langgraph_pipeline()`, `real_ragas_evaluate()`). This is intentional: learn the concepts for free, then flip one class when you have API keys.

---

## 3. Architecture

```
qa-agentic-automation-framework/
├── src/
│   ├── config/settings.py        # Single source of truth for URLs, timeouts, quality thresholds
│   ├── core/                     # Shared OOP base classes + logger
│   ├── api_automation/           # APIClient (retry-aware requests wrapper) + endpoint constants
│   ├── e2e_automation/           # Playwright BasePage + concrete Page Objects
│   ├── ml_validation/            # Model training + evaluation (accuracy/precision/recall/F1/CI)
│   ├── rag_evaluation/           # Multi-agent RAG: Retriever → Generator → Critic agents
│   │   ├── agents.py             # AgentState + the 3 agents (graph nodes)
│   │   ├── graph_pipeline.py     # Orchestrates the agent graph + retry loop
│   │   ├── retriever.py          # TF-IDF retriever (+ ChromaRetriever reference stub)
│   │   ├── llm_client.py         # MockLLM (+ RealLangChainLLM reference stub)
│   │   └── ragas_metrics.py      # faithfulness / relevancy / context precision & recall
│   └── quality_gates/gate_checker.py   # Generic PASS/FAIL gate engine
├── tests/
│   ├── api/    → pytest -m api
│   ├── e2e/    → pytest -m e2e
│   ├── ml/     → pytest -m ml      (quality-gated)
│   └── rag/    → pytest -m rag     (quality-gated, golden dataset)
├── scripts/run_quality_gates.py  # CLI: trains model + runs RAG pipeline → single PASS/FAIL report
└── .github/workflows/ci.yml      # Runs all suites + gate on every push/PR
```

### The Multi-Agent RAG flow

```
question
   │
   ▼
┌─────────────────┐     retrieves top-k docs (TF-IDF similarity)
│ RetrieverAgent   │
└────────┬─────────┘
         ▼
┌─────────────────┐     drafts an answer strictly from retrieved context
│ GeneratorAgent   │◄────────────────────┐
└────────┬─────────┘                     │ retry (max 2 attempts)
         ▼                               │
┌─────────────────┐   scores faithfulness │
│ CriticAgent      │───& relevancy────────┘
└────────┬─────────┘
         ▼
   approved / rejected + full audit trace
```

This mirrors LangGraph's `StateGraph`: a shared `AgentState` object flows through nodes, with a conditional edge that loops back to the Generator when the Critic rejects the draft.

---

## 4. Getting started

```bash
git clone <your-fork-url>
cd qa-agentic-automation-framework
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium   # only needed for E2E tests
```

### Run everything

```bash
pytest                                    # all suites
pytest -m api                             # API tests only
pytest -m e2e                             # Playwright E2E only
pytest -m ml                              # ML model quality-gate tests
pytest -m rag                             # Multi-agent RAG quality-gate tests
python scripts/run_quality_gates.py       # standalone PASS/FAIL release gate report
```

No API keys, no accounts, no paid services required — everything runs against free public sandboxes (`reqres.in` for API, `the-internet.herokuapp.com` for E2E) or fully offline (ML + RAG).

---

## 5. How the Quality Gates work

`scripts/run_quality_gates.py` is what a release pipeline actually calls. It:

1. Trains and evaluates the Logistic Regression complaint classifier — checks accuracy, precision, recall, F1, and a **95% bootstrap confidence interval** on accuracy.
2. Runs the multi-agent RAG pipeline against a hand-curated **golden dataset** (question → expected relevant document) — checks average context precision/recall.
3. Prints one consolidated report and **exits with code 1 if anything fails**, so CI blocks the merge automatically.

Thresholds are centralized in `src/config/settings.py` (`MLQualityGate`, `RAGQualityGate`) — change them in one place to tighten or relax the release bar.

---

## 6. Teaching notes for juniors

- **Start here:** `src/core/base_test.py` — see how OOP inheritance removes duplicate setup/logging code across every suite.
- **Then:** `src/api_automation/api_client.py` — a real retry-aware REST client, not a toy `requests.get()`.
- **Then:** `src/e2e_automation/` — classic Page Object Model; add a new page by extending `BasePage`.
- **Then:** `src/ml_validation/` — this is what "verifying performance within confidence intervals" actually looks like in code.
- **Finally:** `src/rag_evaluation/` — read `agents.py` → `graph_pipeline.py` → `ragas_metrics.py` in that order to understand the full agentic evaluation loop.
- Every "reference-only" docstring (`RealLangChainLLM`, `ChromaRetriever`, `build_langgraph_pipeline`, `real_ragas_evaluate`) shows the exact code you'd write once you have real API keys — treat those as your "next step" exercises.

---

## 7. Extending this repo (suggested exercises for juniors)

1. Add a new Page Object + E2E test for a different flow on the-internet.herokuapp.com.
2. Add a new API test suite for the `/register` and `/login` endpoints (`AuthEndpoints`).
3. Swap `MockLLM` for `RealLangChainLLM` using a real `ChatOpenAI` model and compare faithfulness scores.
4. Add a `context_f1` metric to `ragas_metrics.py` and wire it into the quality gate.
5. Add a 4th agent — a `RewriterAgent` that reformulates the question when the Critic rejects twice.

---

## 8. Author

**Hemant Kumar Dhote** — Principal Software Engineer / Lead Tech (QTE), 10+ years in Test Automation, Agentic RAG Evaluation, and Team Leadership.
