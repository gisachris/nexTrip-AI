# PR Description: Phase 5 - Frameworks & Orchestration

This PR implements Phase 5 of **nexTrip AI**, introducing a Tool-Using AI Agent powered by **LangChain** and **LangGraph** to dynamically orchestrate external services, travel knowledge retrieval, and itinerary generation.

### Key Changes

1. **Agent Dependencies (`pyproject.toml`)**
   - Integrated `langchain`, `langchain-core`, `langchain-anthropic`, and `langgraph`.

2. **Core Agent Tools (`src/nextrip_ai/core/agent/tools.py`)**
   - Added LangChain tools for destination weather (`get_weather_tool`), travel knowledge RAG (`search_travel_knowledge_tool`), point-of-interest discovery (`search_places_tool`), expense estimation (`estimate_travel_cost_tool`), and structured output formatting (`generate_itinerary_tool`).

3. **LangGraph State Graph (`src/nextrip_ai/core/agent/graph.py`)**
   - Created a stateful graph (`StateGraph`) governing agent reasoning, tool execution, output extraction, schema validation, and retry loops.

4. **API Endpoints & Schemas (`src/nextrip_ai/api/routes/itineraries/router.py`)**
   - Refactored `POST /itineraries/` to delegate creation to `agent_graph`.
   - Introduced `POST /itineraries/agent/query` for interactive tool-augmented queries.

5. **Testing & Documentation**
   - Added `tests/test_agent.py` test suite covering agent tools and workflow execution.
   - Updated `README.md` with Phase 5 architecture, tool details, and API documentation.
