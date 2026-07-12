from langgraph.graph import END, START, StateGraph

from .nodes import analyze_user_request, create_agent_response
from .travel_state import TravelAgentState


def build_travel_graph():
    """여행 Agent용 LangGraph를 생성합니다.

    현재 그래프 흐름:

    START
      → analyze_user_request
      → create_agent_response
      → END

    각 노드의 역할:
    - analyze_user_request:
        사용자의 입력을 분석해서 의도와 대상 Day를 찾습니다.

    - create_agent_response:
        분석 결과를 바탕으로 UI에 보여줄 Agent 응답을 만듭니다.
    """

    graph_builder = StateGraph(TravelAgentState)

    # 노드를 등록합니다.
    # 첫 번째 인자는 그래프 안에서 사용할 노드 이름입니다.
    # 두 번째 인자는 실제 실행할 Python 함수입니다.
    graph_builder.add_node("analyze_user_request", analyze_user_request)
    graph_builder.add_node("create_agent_response", create_agent_response)

    # 그래프 시작 지점에서 analyze_user_request 노드로 이동합니다.
    graph_builder.add_edge(START, "analyze_user_request")

    # 요청 분석이 끝나면 응답 생성 노드로 이동합니다.
    graph_builder.add_edge("analyze_user_request", "create_agent_response")

    # 응답 생성이 끝나면 그래프를 종료합니다.
    graph_builder.add_edge("create_agent_response", END)

    # compile()을 해야 실제 실행 가능한 그래프 객체가 됩니다.
    return graph_builder.compile()


# 앱에서 매번 그래프를 새로 만들지 않도록 한 번만 컴파일해 둡니다.
travel_graph = build_travel_graph()


def run_travel_agent(
    user_message: str,
    selected_day_number: int,
    destination_name: str = "제주",
) -> str:
    """UI에서 호출하기 쉽게 만든 LangGraph 실행 함수입니다.

    dashboard_view.py가 LangGraph 내부 구조를 몰라도 되도록,
    이 함수가 입력값을 받아 graph.invoke()를 실행하고
    최종 agent_response 문자열만 반환합니다.
    """

    result = travel_graph.invoke(
        {
            "user_message": user_message,
            "selected_day_number": selected_day_number,
            "destination_name": destination_name,
        }
    )

    return result["agent_response"]