from langgraph.graph import StateGraph, END
from app.agent.state import AgentState
from app.agent.nodes import (
    retrieve, grade_documents, generate, transform_query, 
    router_node, action_iching, action_horoscope
)

def create_graph():
    workflow = StateGraph(AgentState)

    # Define the nodes
    workflow.add_node("retrieve", retrieve)
    workflow.add_node("grade_documents", grade_documents)
    workflow.add_node("generate", generate)
    workflow.add_node("transform_query", transform_query)
    workflow.add_node("action_iching", action_iching)
    workflow.add_node("action_horoscope", action_horoscope)
    # workflow.add_node("router", router_node) # Router logic is in the conditional edge

    # Define the edges
    workflow.set_entry_point("retrieve") # Simplification: Start with retrieve or router
    
    # We can use a conditional entry point
    # workflow.set_conditional_entry_point(
    #     router_node,
    #     {
    #         "action_iching": "action_iching",
    #         "action_horoscope": "action_horoscope",
    #         "retrieve": "retrieve",
    #         "generate": "generate"
    #     }
    # )

    workflow.add_edge("retrieve", "grade_documents")
    
    def check_relevance(state):
        if state.get("next_step") == "transform_query":
            return "transform_query"
        return "generate"

    workflow.add_conditional_edges(
        "grade_documents",
        check_relevance,
        {
            "transform_query": "transform_query",
            "generate": "generate"
        }
    )

    workflow.add_edge("transform_query", "retrieve")
    workflow.add_edge("generate", END)
    workflow.add_edge("action_iching", END)
    workflow.add_edge("action_horoscope", END)

    # Compile
    app = workflow.compile()
    return app
