import os
import re
from pathlib import Path
from typing import Literal
from dotenv import load_dotenv
from Graph.travel_state import ItineraryDay, TravelAgentState, TravelCondition

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE_PATH = PROJECT_ROOT / ".env"

load_dotenv(dotenv_path=ENV_FILE_PATH)


MAX_TRIP_DAY_COUNT = 31


def clamp_trip_day_count(trip_day_count: int | None) -> int | None:
    """너무 큰 Day 수가 UI를 망가뜨리지 않도록 안전 범위를 적용합니다."""

    if trip_day_count is None:
        return None

    if trip_day_count < 1:
        return None

    return min(trip_day_count, MAX_TRIP_DAY_COUNT)


def extract_numeric_trip_day_count(user_message: str) -> int | None:
    """LLM을 쓸 수 없을 때를 위한 최소 fallback 일수 추출입니다.

    이 함수는 후보 키워드 기반 판단을 하지 않습니다.
    숫자로 명확히 표현된 여행 기간만 추출합니다.

    예:
    - 4박 5일 → 5
    - 5일 여행 → 5
    - 2주 여행 → 14
    """

    compact_user_message = user_message.replace(" ", "")

    nights_days_match = re.search(r"(\d+)박(\d+)일", compact_user_message)

    if nights_days_match:
        return clamp_trip_day_count(int(nights_days_match.group(2)))

    day_count_match = re.search(r"(\d+)일", compact_user_message)

    if day_count_match:
        return clamp_trip_day_count(int(day_count_match.group(1)))

    week_count_match = re.search(r"(\d+)주", compact_user_message)

    if week_count_match:
        return clamp_trip_day_count(int(week_count_match.group(1)) * 7)

    return None


def extract_numeric_target_day_number(
    user_message: str,
    selected_day_number: int,
) -> int:
    """LLM을 쓸 수 없을 때를 위한 최소 fallback 대상 Day 추출입니다.

    7일까지만 처리하지 않고 숫자 기반으로 제한 없이 처리합니다.

    예:
    - Day 12
    - 12일차
    - 12번째 날
    """

    day_patterns = [
        r"[Dd]ay\s*(\d+)",
        r"(\d+)일차",
        r"(\d+)번째날",
        r"(\d+)번째\s*날",
        r"(\d+)째날",
        r"(\d+)째\s*날",
    ]

    compact_user_message = user_message.replace(" ", "")

    for day_pattern in day_patterns:
        day_match = re.search(day_pattern, compact_user_message)

        if day_match:
            return int(day_match.group(1))

    return selected_day_number


def build_empty_itinerary_days(trip_day_count: int) -> list[ItineraryDay]:
    """총 여행 일수에 맞춰 빈 Day 일정을 생성합니다.

    3일 고정이 아니라 trip_day_count만큼 동적으로 생성합니다.
    """

    itinerary_days: list[ItineraryDay] = []

    for day_number in range(1, trip_day_count + 1):
        itinerary_days.append(
            {
                "day_number": day_number,
                "title": f"Day {day_number}",
                "items": [],
            }
        )

    return itinerary_days


def create_travel_condition(
    category: str,
    label: str,
    raw_text: str,
    confidence: float = 1.0,
) -> TravelCondition:
    """UI 칩으로 표시할 여행 조건 객체를 만듭니다."""

    return {
        "category": category,
        "label": label,
        "raw_text": raw_text,
        "confidence": confidence,
    }


def deduplicate_travel_conditions(
    travel_conditions: list[TravelCondition],
) -> list[TravelCondition]:
    """중복 조건 칩을 제거합니다."""

    unique_conditions: list[TravelCondition] = []
    seen_keys: set[tuple[str, str]] = set()

    for travel_condition in travel_conditions:
        condition_key = (
            travel_condition["category"],
            travel_condition["label"],
        )

        if condition_key in seen_keys:
            continue

        seen_keys.add(condition_key)
        unique_conditions.append(travel_condition)

    return unique_conditions


def merge_travel_conditions(
    existing_conditions: list[TravelCondition],
    new_conditions: list[TravelCondition],
) -> list[TravelCondition]:
    """기존 조건과 새로 추출한 조건을 병합합니다."""

    return deduplicate_travel_conditions(
        existing_conditions + new_conditions
    )


def fallback_interpret_user_request(
    state: TravelAgentState,
) -> dict[str, object]:
    """LLM을 사용할 수 없을 때 앱이 죽지 않도록 최소 해석을 수행합니다.

    이 fallback은 의미 판단을 하지 않습니다.
    명확한 숫자 기간과 Day 번호만 추출하고,
    나머지는 사용자 요청 원문을 하나의 조건으로 보관합니다.
    """

    user_message = state["user_message"]
    selected_day_number = state["selected_day_number"]

    trip_day_count = extract_numeric_trip_day_count(user_message)
    target_day_number = extract_numeric_target_day_number(
        user_message=user_message,
        selected_day_number=selected_day_number,
    )

    travel_conditions = list(state.get("travel_conditions", []))

    if trip_day_count is not None:
        travel_conditions = merge_travel_conditions(
            existing_conditions=travel_conditions,
            new_conditions=[
                create_travel_condition(
                    category="duration",
                    label=f"{trip_day_count}일 여행",
                    raw_text=user_message,
                    confidence=0.7,
                )
            ],
        )

    if user_message:
        travel_conditions = merge_travel_conditions(
            existing_conditions=travel_conditions,
            new_conditions=[
                create_travel_condition(
                    category="raw_request",
                    label=user_message[:24],
                    raw_text=user_message,
                    confidence=0.4,
                )
            ],
        )

    result: dict[str, object] = {
        "user_intent": "create_initial_trip"
        if trip_day_count is not None
        else "general_question",
        "target_day_number": target_day_number,
        "travel_conditions": travel_conditions,
    }

    if trip_day_count is not None:
        result["trip_day_count"] = trip_day_count
        result["itinerary_days"] = build_empty_itinerary_days(trip_day_count)

    return result


def interpret_user_request_with_llm(
    state: TravelAgentState,
) -> dict[str, object] | None:
    """LLM을 사용해 사용자 요청을 자유 구조로 해석합니다.

    핵심 원칙:
    - 여행지는 제주로 고정하지 않습니다.
    - 동행자, 교통, 숙소, 취향 후보 목록을 코드에 박지 않습니다.
    - category는 내부 분류일 뿐이고, UI에는 label을 표시합니다.
    - Day 번호는 7일 제한 없이 숫자로 추출합니다.
    """

    if not os.getenv("OPENAI_API_KEY"):
        return None

    try:
        from langchain_openai import ChatOpenAI
        from pydantic import BaseModel, Field
    except ImportError:
        return None

    class TravelConditionExtraction(BaseModel):
        category: str = Field(
            description=(
                "Condition category. Examples: destination, duration, companion, "
                "transport, lodging, preference, budget, accessibility, food, "
                "schedule, pace, constraint, other. You may create a new category "
                "if needed."
            )
        )
        label: str = Field(
            description=(
                "Short Korean UI chip label. Examples: 부모님 동반, 반려견 동반, "
                "조용한 숙소, 해변 위주, 휠체어 이동 고려."
            )
        )
        raw_text: str = Field(
            description="Exact or near-exact phrase from the user message."
        )
        confidence: float = Field(
            ge=0.0,
            le=1.0,
            description="Confidence score from 0.0 to 1.0.",
        )

    class TravelRequestInterpretation(BaseModel):
        user_intent: Literal[
            "create_initial_trip",
            "change_itinerary",
            "recommend_place",
            "check_route",
            "update_condition",
            "general_question",
        ] = Field(description="Main intent of the user message.")
        destination_name: str | None = Field(
            default=None,
            description=(
                "Travel destination if explicitly mentioned or strongly implied. "
                "Do not default to Jeju."
            ),
        )
        trip_day_count: int | None = Field(
            default=None,
            description=(
                "Total number of trip days. 4박5일 means 5. "
                "If not clear, return null."
            ),
        )
        trip_duration_label: str | None = Field(
            default=None,
            description=(
                "Original duration label for UI, such as 4박 5일, 2주, 당일치기. "
                "If not clear, return null."
            ),
        )
        target_day_number: int | None = Field(
            default=None,
            description=(
                "Specific Day number referenced by user. Support any positive number. "
                "For example Day 12 or 12일차 means 12."
            ),
        )
        travel_conditions: list[TravelConditionExtraction] = Field(
            default_factory=list,
            description=(
                "All meaningful trip conditions from the user text. "
                "Do not rely on a fixed candidate list. Extract arbitrary meaningful "
                "conditions and preserve raw text."
            ),
        )
        agent_response: str = Field(
            description="Short Korean response to show in the chat panel."
        )

    current_context = {
        "selected_day_number": state.get("selected_day_number"),
        "destination_name": state.get("destination_name"),
        "trip_day_count": state.get("trip_day_count"),
        "travel_conditions": state.get("travel_conditions", []),
        "itinerary_days_count": len(state.get("itinerary_days", [])),
    }

    system_prompt = """
너는 여행 플래너 앱의 자연어 구조화 노드다.

절대 후보 목록 기반으로만 판단하지 마라.
사용자 문장 안의 의미 단위를 읽고, UI에 표시할 짧은 조건 label을 만들어라.

규칙:
1. 여행지는 제주로 기본 설정하지 않는다. 명시되거나 강하게 암시될 때만 destination_name에 넣는다.
2. 가족, 부모님, 아이, 친구, 커플 같은 정해진 후보에 묶이지 않는다.
   예: 할머니, 반려견, 직장 동료, 혼자 조용히, 휠체어 이동 고려 등도 조건으로 추출한다.
3. 교통수단도 렌터카/버스 후보에 묶이지 않는다.
   예: 전기차, 택시 위주, 유모차 이동, 도보 최소화 등도 조건으로 추출한다.
4. 숙소 지역도 후보 목록에 묶이지 않는다.
   사용자가 말한 지역/숙소 표현을 그대로 조건으로 보관한다.
5. 취향도 후보 목록에 묶이지 않는다.
   조용한 곳, 사진 잘 나오는 곳, 부모님이 걷기 편한 곳, 비 오는 날 가능한 곳 등 자유롭게 추출한다.
6. Day 번호는 7일 제한 없이 추출한다.
   예: 12일차, Day 12, 열흘째 같은 표현도 가능한 만큼 숫자로 해석한다.
7. UI chip label은 짧고 자연스러운 한국어로 만든다.
8. raw_text에는 사용자 원문 근거를 넣는다.
9. 확실하지 않은 것은 confidence를 낮게 주고, 억지로 만들지 않는다.
"""

    user_prompt = f"""
현재 앱 상태:
{current_context}

사용자 입력:
{state["user_message"]}
"""

    model_name = os.getenv("TRAVEL_AGENT_MODEL", "gpt-4o-mini")

    chat_model = ChatOpenAI(
        model=model_name,
        temperature=0,
    )

    structured_model = chat_model.with_structured_output(
        TravelRequestInterpretation
    )

    interpretation = structured_model.invoke(
        [
            ("system", system_prompt),
            ("human", user_prompt),
        ]
    )

    new_conditions: list[TravelCondition] = []

    if interpretation.destination_name:
        new_conditions.append(
            create_travel_condition(
                category="destination",
                label=f"{interpretation.destination_name} 여행",
                raw_text=interpretation.destination_name,
                confidence=1.0,
            )
        )

    if interpretation.trip_day_count is not None:
        duration_label = (
            interpretation.trip_duration_label
            or f"{interpretation.trip_day_count}일 여행"
        )

        new_conditions.append(
            create_travel_condition(
                category="duration",
                label=duration_label,
                raw_text=duration_label,
                confidence=1.0,
            )
        )

    for condition in interpretation.travel_conditions:
        new_conditions.append(
            create_travel_condition(
                category=condition.category,
                label=condition.label,
                raw_text=condition.raw_text,
                confidence=condition.confidence,
            )
        )

    existing_conditions = list(state.get("travel_conditions", []))
    merged_conditions = merge_travel_conditions(
        existing_conditions=existing_conditions,
        new_conditions=new_conditions,
    )

    result: dict[str, object] = {
        "user_intent": interpretation.user_intent,
        "travel_conditions": merged_conditions,
        "agent_response": interpretation.agent_response,
    }

    if interpretation.destination_name:
        result["destination_name"] = interpretation.destination_name

    trip_day_count = clamp_trip_day_count(interpretation.trip_day_count)

    if trip_day_count is not None:
        result["trip_day_count"] = trip_day_count

        if interpretation.user_intent == "create_initial_trip":
            result["itinerary_days"] = build_empty_itinerary_days(
                trip_day_count
            )

    if interpretation.target_day_number is not None:
        result["target_day_number"] = interpretation.target_day_number
    else:
        result["target_day_number"] = extract_numeric_target_day_number(
            user_message=state["user_message"],
            selected_day_number=state["selected_day_number"],
        )

    return result


def analyze_user_request(state: TravelAgentState) -> dict[str, object]:
    """사용자 입력을 분석하는 LangGraph 노드입니다."""

    llm_result = interpret_user_request_with_llm(state)

    if llm_result is not None:
        return llm_result

    return fallback_interpret_user_request(state)


def create_agent_response(state: TravelAgentState) -> dict[str, str]:
    """Agent 응답 문장을 만드는 LangGraph 노드입니다.

    LLM 해석 단계에서 이미 agent_response가 있으면 그대로 사용합니다.
    fallback일 때만 기본 응답을 만듭니다.
    """

    existing_agent_response = state.get("agent_response")

    if existing_agent_response:
        return {
            "agent_response": existing_agent_response,
        }

    user_intent = state.get("user_intent", "general_question")
    travel_conditions = state.get("travel_conditions", [])

    if user_intent == "create_initial_trip":
        condition_labels = [
            condition["label"]
            for condition in travel_conditions
        ]

        condition_summary = ", ".join(condition_labels)

        return {
            "agent_response": (
                f"여행 조건을 저장했습니다. 현재 조건은 {condition_summary}입니다. "
                "이제 각 Day별 장소 추천과 동선 구성을 이어서 만들 수 있습니다."
            )
        }

    return {
        "agent_response": (
            "요청을 확인했습니다. 필요한 조건은 여행 조건 칩에 저장하고, "
            "이후 일정 생성 단계에 반영하겠습니다."
        )
    }