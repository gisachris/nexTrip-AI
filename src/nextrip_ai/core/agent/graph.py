import logging
from typing import Dict, Any, List, Optional, TypedDict, Annotated
from pydantic import ValidationError

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage, ToolMessage
from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from nextrip_ai.core.config import settings
from nextrip_ai.core.agent.tools import (
    agent_tools,
    get_weather_tool,
    search_travel_knowledge_tool,
    search_places_tool,
    estimate_travel_cost_tool,
    generate_itinerary_tool
)
from nextrip_ai.api.routes.itineraries.schema import AIItinerarySchema

logger = logging.getLogger(__name__)

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    destination: str
    days: int
    budget: float
    trip_style: str
    itinerary_data: Optional[Dict[str, Any]]
    validation_errors: List[str]
    attempts: int

def validate_itinerary_data(data: dict, destination: str, days: int, budget: float) -> List[str]:
    errors = []
    if not data:
        return ["No itinerary data produced."]
        
    try:
        validated = AIItinerarySchema.model_validate(data)
    except ValidationError as e:
        for err in e.errors():
            loc = " -> ".join(str(x) for x in err["loc"])
            errors.append(f"Schema validation error at '{loc}': {err['msg']}")
        return errors
        
    if len(validated.days) != days:
        errors.append(f"Day count ({len(validated.days)}) does not match requested trip duration ({days})")
        
    dest = validated.destination
    if destination.lower() not in dest.lower() and dest.lower() not in destination.lower():
        errors.append(f"Destination '{dest}' does not match trip destination '{destination}'")
        
    est_total = validated.estimated_total_cost
    limit = budget * 1.10
    if est_total > limit:
        errors.append(f"Estimated total cost ${est_total:.2f} exceeds budget ${budget:.2f} by more than 10% (limit: ${limit:.2f})")
        
    return errors

def get_llm():
    if not settings.ANTHROPIC_API_KEY or "mock" in settings.ANTHROPIC_API_KEY.lower():
        return None
    return ChatAnthropic(
        model="claude-3-5-haiku-20241022",
        anthropic_api_key=settings.ANTHROPIC_API_KEY,
        temperature=0.3,
        max_tokens=4000
    )

def agent_node(state: AgentState) -> Dict[str, Any]:
    llm = get_llm()
    
    if llm is None:
        dest = state.get("destination", "Paris")
        days_cnt = state.get("days", 2)
        budget = state.get("budget", 1000.0)
        style = state.get("trip_style", "Cultural")
        
        mock_data = {
            "title": f"Explore {dest}",
            "destination": dest,
            "travel_style": style,
            "budget": budget,
            "estimated_total_cost": min(budget * 0.85, 800.0),
            "days": [
                {
                    "day_number": i + 1,
                    "theme": f"Highlights of {dest} - Day {i + 1}",
                    "estimated_cost": min(budget * 0.85, 800.0) / days_cnt,
                    "activities": [
                        {
                            "time": "Morning",
                            "activity": f"Visit landmark {i + 1}A",
                            "location": f"Center {dest}",
                            "description": "Explore city center sights.",
                            "estimated_cost": 50.0
                        },
                        {
                            "time": "Afternoon",
                            "activity": f"Local experience {i + 1}B",
                            "location": f"Old Town {dest}",
                            "description": "Enjoy local cuisine and culture.",
                            "estimated_cost": 50.0
                        }
                    ]
                } for i in range(days_cnt)
            ]
        }
        
        tool_call_msg = AIMessage(
            content="Generated itinerary via tool call.",
            tool_calls=[{
                "name": "generate_itinerary_tool",
                "args": mock_data,
                "id": "mock_call_1"
            }]
        )
        return {"messages": [tool_call_msg]}

    llm_with_tools = llm.bind_tools(agent_tools)
    
    sys_prompt = SystemMessage(content=(
        "You are an expert, tool-using AI Travel Assistant.\n"
        "Your goal is to plan personalized travel itineraries using available tools.\n\n"
        "Guidelines:\n"
        "1. First, check destination weather using `get_weather_tool`.\n"
        "2. Retrieve relevant travel guides using `search_travel_knowledge_tool`.\n"
        "3. Find popular attractions using `search_places_tool`.\n"
        "4. Estimate travel expenses using `estimate_travel_cost_tool`.\n"
        "5. Finally, synthesize all retrieved context and submit the finished itinerary via `generate_itinerary_tool`.\n"
        "6. Always keep estimated total cost within the specified budget."
    ))
    
    messages = [sys_prompt] + list(state["messages"])
    try:
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}
    except Exception as e:
        logger.warning(f"LLM call failed with error: {e}. Falling back to mock itinerary generator.")
        dest = state.get("destination", "Paris")
        days_cnt = state.get("days", 2)
        budget = state.get("budget", 1000.0)
        style = state.get("trip_style", "Cultural")
        
        mock_data = {
            "title": f"Explore {dest}",
            "destination": dest,
            "travel_style": style,
            "budget": budget,
            "estimated_total_cost": min(budget * 0.85, 800.0),
            "days": [
                {
                    "day_number": i + 1,
                    "theme": f"Highlights of {dest} - Day {i + 1}",
                    "estimated_cost": min(budget * 0.85, 800.0) / days_cnt,
                    "activities": [
                        {
                            "time": "Morning",
                            "activity": f"Visit landmark {i + 1}A",
                            "location": f"Center {dest}",
                            "description": "Explore city center sights.",
                            "estimated_cost": 50.0
                        },
                        {
                            "time": "Afternoon",
                            "activity": f"Local experience {i + 1}B",
                            "location": f"Old Town {dest}",
                            "description": "Enjoy local cuisine and culture.",
                            "estimated_cost": 50.0
                        }
                    ]
                } for i in range(days_cnt)
            ]
        }
        
        tool_call_msg = AIMessage(
            content=f"Generated itinerary via tool call (Fallback mode: {str(e)}).",
            tool_calls=[{
                "name": "generate_itinerary_tool",
                "args": mock_data,
                "id": "mock_call_fallback"
            }]
        )
        return {"messages": [tool_call_msg]}

tool_node = ToolNode(agent_tools)

def extract_itinerary_node(state: AgentState) -> Dict[str, Any]:
    itinerary_data = state.get("itinerary_data")
    last_msg = state["messages"][-1]
    
    if isinstance(last_msg, AIMessage) and last_msg.tool_calls:
        for tc in last_msg.tool_calls:
            if tc["name"] == "generate_itinerary_tool":
                itinerary_data = tc["args"]
                break
                
    errors = []
    if itinerary_data:
        errors = validate_itinerary_data(
            itinerary_data,
            state["destination"],
            state["days"],
            state["budget"]
        )
        
    attempts = state.get("attempts", 0) + 1
    
    res = {
        "itinerary_data": itinerary_data,
        "validation_errors": errors,
        "attempts": attempts
    }
    
    if errors and attempts < 3:
        feedback = (
            "The generated itinerary had validation issues:\n"
            + "\n".join(f"- {e}" for e in errors)
            + "\nPlease fix these issues and invoke `generate_itinerary_tool` again."
        )
        res["messages"] = [HumanMessage(content=feedback)]
        
    return res

def should_continue(state: AgentState) -> str:
    messages = state["messages"]
    last_msg = messages[-1]
    
    if isinstance(last_msg, AIMessage) and last_msg.tool_calls:
        for tc in last_msg.tool_calls:
            if tc["name"] == "generate_itinerary_tool":
                return "extract_itinerary"
        return "tools"
        
    errors = state.get("validation_errors", [])
    attempts = state.get("attempts", 0)
    itinerary_data = state.get("itinerary_data")
    
    if itinerary_data and not errors:
        return END
        
    if errors and attempts < 3:
        return "agent"
        
    return END

workflow = StateGraph(AgentState)

workflow.add_node("agent", agent_node)
workflow.add_node("tools", tool_node)
workflow.add_node("extract_itinerary", extract_itinerary_node)

workflow.set_entry_point("agent")

workflow.add_conditional_edges("agent", should_continue, {
    "tools": "tools",
    "extract_itinerary": "extract_itinerary",
    END: END
})

workflow.add_edge("tools", "agent")
workflow.add_conditional_edges("extract_itinerary", lambda s: "agent" if (s.get("validation_errors") and s.get("attempts", 0) < 3) else END, {
    "agent": "agent",
    END: END
})

agent_graph = workflow.compile()
