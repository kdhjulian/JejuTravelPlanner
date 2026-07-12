from .travel_state import TravelAgentState, TravelUserIntent


def extract_target_day_number(user_message: str, selected_day_number: int) -> int:
    """사용자 문장에서 대상 Day 번호를 추출합니다.

    예:
    - "첫째 날 바꿔줘" → 1
    - "둘째 날은 애월 중심으로 바꿔줘" → 2
    - "셋째 날 일정 추천해줘" → 3

    사용자가 날짜를 말하지 않으면 현재 UI에서 선택된 Day 번호를 그대로 사용합니다.
    """

    compact_user_message = user_message.replace(" ", "")

    if any(
        keyword in compact_user_message
        for keyword in ["첫째날", "1일차", "Day1", "day1"]
    ):
        return 1
    
    if any(
        keyword in compact_user_message
        for keyword in ["둘째날", "2일차", "Day2", "day2"]
    ):
        return 2
    
    if any(
        keyword in compact_user_message
        for keyword in ["셋째날", "3일차", "Day3", "day3"]
    ):
        return 2

    return selected_day_number


def classify_user_intent(user_message: str) -> TravelUserIntent:
    """사용자 요청 의도를 간단한 규칙으로 분류합니다.

    지금은 LLM을 쓰지 않습니다.
    먼저 UI → LangGraph → UI 연결을 검증하는 단계이기 때문입니다.

    나중에는 이 함수를 OpenAI structured output 기반 분류기로 교체할 수 있습니다.
    """

    compact_user_message = user_message.replace(" ", "")

    if any(
        keyword in compact_user_message
        for keyword in ["바꿔", "수정", "변경", "조정", "빼줘", "넣어줘"]
    ):
        return "change_itinerary"

    if any(
        keyword in compact_user_message
        for keyword in ["추천", "어디", "장소", "카페", "맛집", "관광지"]
    ):
        return "recommend_place"

    if any(
        keyword in compact_user_message
        for keyword in ["경로", "동선", "이동", "거리", "너무멀어"]
    ):
        return "check_route"

    return "general_question"


def analyze_user_request(state: TravelAgentState) -> dict[str, object]:
    """사용자 입력을 분석하는 LangGraph 노드입니다.

    입력 state에서 user_message와 selected_day_number를 읽고,
    아래 두 값을 새로 추가합니다.

    - user_intent
    - target_day_number

    이 노드는 아직 UI를 수정하지 않습니다.
    단지 사용자의 요청을 이해하는 역할만 합니다.
    """

    user_message = state["user_message"]
    selected_day_number = state["selected_day_number"]

    user_intent = classify_user_intent(user_message)
    target_day_number = extract_target_day_number(
        user_message=user_message,
        selected_day_number=selected_day_number,
    )

    return {
        "user_intent": user_intent,
        "target_day_number": target_day_number,
    }


def create_agent_response(state: TravelAgentState) -> dict[str, str]:
    """Agent 응답 문장을 만드는 LangGraph 노드입니다.

    analyze_user_request 노드가 만든 user_intent와 target_day_number를 읽어서
    오른쪽 Agent 패널에 표시할 문장을 생성합니다.

    지금은 실제 일정 데이터를 수정하지 않고,
    사용자의 요청을 어떻게 이해했는지만 응답합니다.
    """

    user_message = state["user_message"]
    destination_name = state["destination_name"]
    user_intent = state.get("user_intent", "general_question")
    target_day_number = state.get("target_day_number", state["selected_day_number"])

    if user_intent == "change_itinerary":
        agent_response = (
            f"{destination_name} 여행 Day {target_day_number} 일정 수정 요청으로 이해했습니다. "
            f"입력하신 내용은 '{user_message}'입니다. "
            "다음 단계에서 이 요청을 실제 일정 카드 수정으로 연결하겠습니다."
        )

    elif user_intent == "recommend_place":
        agent_response = (
            f"{destination_name} 여행 Day {target_day_number}에 추가할 장소 추천 요청으로 이해했습니다. "
            "다음 단계에서 후보 장소를 일정 카드 형태로 제안하겠습니다."
        )

    elif user_intent == "check_route":
        agent_response = (
            f"{destination_name} 여행 Day {target_day_number}의 경로 또는 동선 확인 요청으로 이해했습니다. "
            "다음 단계에서 지도 영역의 경로 검증 결과와 연결하겠습니다."
        )

    else:
        agent_response = (
            f"{destination_name} 여행 관련 요청으로 확인했습니다. "
            "일정 수정, 장소 추천, 경로 확인 중 어떤 작업인지 조금 더 구체적으로 입력하면 "
            "더 정확히 도와드릴 수 있습니다."
        )

    return {
        "agent_response": agent_response,
    }