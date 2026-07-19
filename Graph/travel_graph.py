"""
Graph/travel_graph.py — LangGraph 워크플로우 정의 및 실행 인터페이스

LangGraph의 StateGraph를 사용해 여행 에이전트의 노드·엣지·분기를 선언하고,
컴파일된 그래프 인스턴스를 모듈 수준에서 생성합니다.

그래프 구조 (Mermaid 형식):
    START
      │
      ▼
    guard_jeju_scope ──(blocked)──► create_guardrail_response ──► END
      │
      (allowed)
      │
      ▼
    analyze_user_request
      │
      ▼
    generate_itinerary_cards
      │
      ▼
    create_agent_response ──► END

설계 결정:
    - 가드레일을 첫 번째 노드로 배치하여, 지원하지 않는 여행지 요청이
      비용이 큰 LLM 분석 노드까지 도달하지 않도록 합니다.
    - 그래프는 모듈 로드 시 한 번만 컴파일(build_travel_graph)되어
      travel_graph 싱글턴으로 재사용됩니다.
"""

from langgraph.graph import END, START, StateGraph

from app_config import SUPPORTED_DESTINATION_NAME
from Graph.input_guardrails import guard_jeju_scope
from Graph.nodes import (
    analyze_user_request,
    create_agent_response,
    create_guardrail_response,
    generate_itinerary_cards,
)
from Graph.travel_state import ItineraryDay, TravelAgentState, TravelCondition


# ──────────────────────────────────────────────────────────────
# 조건부 분기(Conditional Edge) 함수
# ──────────────────────────────────────────────────────────────
def route_after_jeju_guardrail(state: TravelAgentState) -> str:
    """제주 전용 guardrail 결과에 따라 다음 노드를 결정합니다.

    LangGraph의 add_conditional_edges()에 전달되는 라우팅 함수입니다.
    state의 guardrail_blocked 값을 확인해 분기합니다.

    Args:
        state: 현재 LangGraph 상태.

    Returns:
        "blocked" → create_guardrail_response 노드로 이동
        "allowed" → analyze_user_request 노드로 이동
    """

    if state.get("guardrail_blocked"):
        return "blocked"

    return "allowed"


# ──────────────────────────────────────────────────────────────
# 그래프 빌드 함수
# ──────────────────────────────────────────────────────────────
def build_travel_graph():
    """여행 Agent용 LangGraph를 생성하고 컴파일합니다.

    Returns:
        CompiledStateGraph — .invoke()로 실행 가능한 컴파일된 그래프.
    """

    graph_builder = StateGraph(TravelAgentState)

    # ── 노드 등록 ────────────────────────────────────────────
    # 각 노드는 (state → partial_state_dict) 시그니처를 가진 함수입니다.
    graph_builder.add_node("guard_jeju_scope", guard_jeju_scope)
    graph_builder.add_node("create_guardrail_response", create_guardrail_response)
    graph_builder.add_node("analyze_user_request", analyze_user_request)
    graph_builder.add_node("create_agent_response", create_agent_response)
    graph_builder.add_node("generate_itinerary_cards", generate_itinerary_cards)

    # ── 엣지(Edge) 연결 ─────────────────────────────────────
    # START → guard_jeju_scope: 모든 요청은 가드레일을 먼저 통과
    graph_builder.add_edge(START, "guard_jeju_scope")

    # 가드레일 통과 여부에 따른 조건부 분기
    graph_builder.add_conditional_edges(
        "guard_jeju_scope",
        route_after_jeju_guardrail,
        {
            "blocked": "create_guardrail_response",   # 차단 → 안내 메시지 생성
            "allowed": "analyze_user_request",         # 통과 → 사용자 요청 분석
        },
    )

    # 차단 경로: 안내 메시지 생성 후 종료
    graph_builder.add_edge("create_guardrail_response", END)

    # 정상 경로: 분석 → 일정 카드 생성 → 에이전트 응답 생성 → 종료
    graph_builder.add_edge("analyze_user_request", "generate_itinerary_cards")
    graph_builder.add_edge("generate_itinerary_cards", "create_agent_response")
    graph_builder.add_edge("create_agent_response", END)

    return graph_builder.compile()


# ──────────────────────────────────────────────────────────────
# 모듈 수준 싱글턴 — 그래프는 한 번만 컴파일
# ──────────────────────────────────────────────────────────────
# 모듈 임포트 시 그래프가 빌드·컴파일됩니다.
# run_travel_agent()는 이 싱글턴을 재사용합니다.
travel_graph = build_travel_graph()


# ──────────────────────────────────────────────────────────────
# UI → LangGraph 실행 인터페이스
# ──────────────────────────────────────────────────────────────
def run_travel_agent(
    user_message: str,
    selected_day_number: int,
    destination_name: str = SUPPORTED_DESTINATION_NAME,
    travel_conditions: list[TravelCondition] | None = None,
    itinerary_days: list[ItineraryDay] | None = None,
    trip_day_count: int | None = None,
) -> TravelAgentState:
    """UI에서 호출하기 쉽게 만든 LangGraph 실행 래퍼(wrapper) 함수입니다.

    UI 레이어(dashboard_view.py)는 이 함수만 호출하면 되며,
    LangGraph의 내부 구조(노드·엣지·상태 스키마)를 알 필요가 없습니다.

    Args:
        user_message:        사용자가 입력한 원본 텍스트.
        selected_day_number: UI에서 현재 선택된 Day 번호.
        destination_name:    여행지 이름 (기본값: "제주").
        travel_conditions:   기존에 누적된 여행 조건 목록 (없으면 빈 리스트).
        itinerary_days:      기존에 생성된 전체 일정 (없으면 빈 리스트).
        trip_day_count:      총 여행 일수 (아직 미정이면 None).

    Returns:
        TravelAgentState — 그래프 실행 완료 후의 최종 상태.
        UI는 이 결과에서 itinerary_days, travel_conditions, agent_response 등을 꺼내
        화면을 갱신합니다.

    NOTE:
        destination_name 매개변수를 받지만 initial_state에서는
        항상 SUPPORTED_DESTINATION_NAME("제주")으로 덮어씁니다.
        현재는 제주 전용이기 때문이며, 향후 여행지 확장 시 이 부분을 수정합니다.
    """

    # ── 초기 상태 조립 ───────────────────────────────────────
    initial_state: TravelAgentState = {
        "user_message": user_message,
        "selected_day_number": selected_day_number,
        "destination_name": SUPPORTED_DESTINATION_NAME,  # 제주 고정
        "travel_conditions": travel_conditions or [],
        "itinerary_days": itinerary_days or [],
    }

    # trip_day_count는 None일 수 있으므로 값이 있을 때만 포함합니다.
    # NotRequired 필드이므로 키 자체가 없는 것과 None이 들어간 것은 의미가 다릅니다.
    if trip_day_count is not None:
        initial_state["trip_day_count"] = trip_day_count

    # ── 그래프 실행 ──────────────────────────────────────────
    # .invoke()는 동기 실행이며, 모든 노드를 순서대로 통과한 최종 상태를 반환합니다.
    result = travel_graph.invoke(initial_state)

    return result
