from langgraph.graph import StateGraph, END
from backend.state import AgentState
from backend.agents import climate_agent, market_agent, feasibility_agent, supervisor_agent

# Create the state graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("supervisor", supervisor_agent)
workflow.add_node("climate_agent", climate_agent)
workflow.add_node("market_agent", market_agent)
workflow.add_node("feasibility_agent", feasibility_agent)

# Set the entry point
workflow.set_entry_point("supervisor")

# Define routing function
def route_next(state: AgentState):
    next_node = state.get("next_node")
    if next_node == "climate_agent":
        return "climate_agent"
    elif next_node == "market_agent":
        return "market_agent"
    elif next_node == "feasibility_agent":
        return "feasibility_agent"
    else:
        return END

# Set up edges
# All worker agents route back to the supervisor to decide the next step
workflow.add_edge("climate_agent", "supervisor")
workflow.add_edge("market_agent", "supervisor")
workflow.add_edge("feasibility_agent", "supervisor")

# The supervisor conditionally routes based on the next_node field
workflow.add_conditional_edges(
    "supervisor",
    route_next,
    {
        "climate_agent": "climate_agent",
        "market_agent": "market_agent",
        "feasibility_agent": "feasibility_agent",
        END: END
    }
)

# Compile the graph
app = workflow.compile()
