"""
MultiAgentRAGPipeline: orchestrates Retriever -> Generator -> Critic in
a graph/loop, the same conceptual shape as a LangGraph `StateGraph`
with a conditional edge ("retry" vs "end").

We hand-roll the state machine here (no LangGraph runtime dependency)
so the pipeline is trivially unit-testable and runs in CI without
network access. The equivalent real LangGraph wiring is shown at the
bottom in `build_langgraph_pipeline()` as a reference for juniors who
want to run this against the real library once installed.
"""
from __future__ import annotations

from src.rag_evaluation.agents import AgentState, RetrieverAgent, GeneratorAgent, CriticAgent
from src.core.logger import get_logger

logger = get_logger("GraphPipeline")


class MultiAgentRAGPipeline:
    def __init__(
        self,
        retriever_agent: RetrieverAgent,
        generator_agent: GeneratorAgent,
        critic_agent: CriticAgent,
        max_attempts: int = 2,
    ):
        self.retriever_agent = retriever_agent
        self.generator_agent = generator_agent
        self.critic_agent = critic_agent
        self.max_attempts = max_attempts

    def run(self, question: str) -> AgentState:
        state = AgentState(question=question)
        state = self.retriever_agent.run(state)

        while True:
            state = self.generator_agent.run(state)
            state = self.critic_agent.run(state)

            if state.approved or state.attempts >= self.max_attempts:
                break
            logger.info("Answer rejected by CriticAgent, retrying generation...")

        return state


def build_langgraph_pipeline():
    """
    Reference-only: how this same graph looks with real LangGraph.
    Not imported/used by the test suite (keeps CI dependency-light).

        from langgraph.graph import StateGraph, END

        def retriever_node(state): ...
        def generator_node(state): ...
        def critic_node(state): ...
        def route(state):
            return END if state["approved"] or state["attempts"] >= 2 else "generator"

        graph = StateGraph(dict)
        graph.add_node("retriever", retriever_node)
        graph.add_node("generator", generator_node)
        graph.add_node("critic", critic_node)
        graph.set_entry_point("retriever")
        graph.add_edge("retriever", "generator")
        graph.add_edge("generator", "critic")
        graph.add_conditional_edges("critic", route, {"generator": "generator", END: END})
        app = graph.compile()
        app.invoke({"question": "..."})
    """
    raise NotImplementedError("Reference implementation only - see docstring.")
