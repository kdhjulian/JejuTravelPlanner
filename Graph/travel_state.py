from typing import Literal, NotRequired, TypedDict


TravelUserIntent = Literal[
    "create_initial_trip",
    "change_itinerary",
    "recommend_place",
    "check_route",
    "update_condition",
    "general_question",
]


class TravelCondition(TypedDict):
    """사용자 자연어에서 추출한 여행 조건입니다.

    category:
        companion, transport, lodging, preference 같은 분류입니다.
        단, 고정 enum이 아니라 LLM이 필요하면 새로운 category를 만들 수 있습니다.

    label:
        UI 칩에 보여줄 짧은 문자열입니다.
        예: "부모님 동반", "렌터카", "애월 숙소", "조용한 여행", "반려견 동반"

    raw_text:
        사용자가 실제로 입력한 원문 근거입니다.

    confidence:
        LLM이 판단한 신뢰도입니다.
    """

    category: str
    label: str
    raw_text: str
    confidence: float


class ItineraryItem(TypedDict):
    """하루 일정 안에 들어가는 장소/활동 카드입니다."""

    time: str
    title: str
    description: str
    travel_time: str


class ItineraryDay(TypedDict):
    """Day 단위 일정입니다."""

    day_number: int
    title: str
    items: list[ItineraryItem]


class TravelAgentState(TypedDict):
    """여행 Agent가 LangGraph 안에서 주고받는 상태입니다."""

    user_message: str
    selected_day_number: int

    destination_name: NotRequired[str]
    user_intent: NotRequired[TravelUserIntent]
    target_day_number: NotRequired[int]

    trip_day_count: NotRequired[int]
    travel_conditions: NotRequired[list[TravelCondition]]
    itinerary_days: NotRequired[list[ItineraryDay]]

    agent_response: NotRequired[str]