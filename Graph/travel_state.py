from typing import Literal, NotRequired, TypedDict

TravelUserIntent = Literal[
    "change_itinerary",
    "recommend_place",
    "check_route",
    "general_question",
]

class TravelAgentState(TypedDict):
    """여행 Agent가 LangGraph 안에서 주고받는 상태입니다.

    LangGraph는 하나의 state를 여러 노드가 이어받으면서 처리합니다.

    예를 들어 UI에서 처음 넘겨주는 값은 이런 형태입니다.

    {
        "user_message": "둘째 날은 애월 중심으로 바꿔줘",
        "selected_day_number": 2,
        "destination_name": "제주"
    }

    이후 analyze_user_request 노드가 user_intent, target_day_number를 추가하고,
    create_agent_response 노드가 agent_response를 추가합니다.
    """

    # 사용자가 오른쪽 Agent 입력창에 입력한 원문입니다.
    user_message: str

    # 현재 UI에서 선택된 Day 번호입니다.
    # dashboard_view.py의 ui_state["selected_day_number"]와 연결됩니다.
    selected_day_number: int

    # 현재 여행 대상 지역입니다.
    # 지금은 "제주"이지만, 나중에 "부산", "강릉", "서울" 등으로 확장할 수 있습니다.
    destination_name: str

    # 사용자의 요청 의도입니다.
    # 처음 입력에는 없고, analyze_user_request 노드가 추가합니다.
    user_intent: NotRequired[TravelUserIntent]

    # 사용자가 특정 날짜를 말했을 때 추출되는 Day 번호입니다.
    # 예: "둘째 날" → 2
    # 사용자가 날짜를 말하지 않으면 selected_day_number를 그대로 사용합니다.
    target_day_number: NotRequired[int]

    # 최종적으로 UI의 오른쪽 Agent 패널에 표시할 응답입니다.
    agent_response: NotRequired[str]