from langgraph.graph import END, START, StateGraph

from Graph.nodes import analyze_user_request, create_agent_response
from Graph.travel_state import ItineraryDay, TravelAgentState, TravelCondition


def build_travel_graph():
    """여행 Agent용 LangGraph를 생성합니다."""

    graph_builder = StateGraph(TravelAgentState)

    graph_builder.add_node("analyze_user_request", analyze_user_request)
    graph_builder.add_node("create_agent_response", create_agent_response)

    graph_builder.add_edge(START, "analyze_user_request")
    graph_builder.add_edge("analyze_user_request", "create_agent_response")
    graph_builder.add_edge("create_agent_response", END)

    return graph_builder.compile()


travel_graph = build_travel_graph()


def run_travel_agent(
    user_message: str,
    selected_day_number: int,
    destination_name: str = "",
    travel_conditions: list[TravelCondition] | None = None,
    itinerary_days: list[ItineraryDay] | None = None,
    trip_day_count: int | None = None,
) -> TravelAgentState:
    """UI에서 호출하기 쉽게 만든 LangGraph 실행 함수입니다."""

    initial_state: TravelAgentState = {
        "user_message": user_message,
        "selected_day_number": selected_day_number,
        "destination_name": destination_name,
        "travel_conditions": travel_conditions or [],
        "itinerary_days": itinerary_days or [],
    }

    if trip_day_count is not None:
        initial_state["trip_day_count"] = trip_day_count

    result = travel_graph.invoke(initial_state)

    return result