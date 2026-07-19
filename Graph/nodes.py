"""
Graph/nodes.py — LangGraph 노드 함수 모음 (핵심 비즈니스 로직)

이 파일은 여행 에이전트의 두뇌에 해당합니다.
사용자 요청 분석, 일정 생성, 일정 수정(전체 교체 / 카드 단위 패치),
에이전트 응답 생성 등 LangGraph 각 노드의 실행 로직을 담고 있습니다.

주요 함수 그룹:
    1. 유틸리티 — 숫자 추출, 조건 병합, 유효성 검사 등
    2. LLM 해석 — interpret_user_request_with_llm / fallback_interpret_user_request
    3. 일정 생성 — generate_itinerary_cards_with_llm
    4. 일정 수정 — patch_itinerary_items_with_llm (카드 단위)
                  modify_itinerary_cards_with_llm (Day 전체 교체)
    5. LangGraph 노드 — analyze_user_request, generate_itinerary_cards,
                        create_agent_response, create_guardrail_response

수정 전략 (2단계):
    사용자가 기존 일정 수정을 요청하면:
    ① 먼저 카드 단위 patch를 시도합니다 (patch_itinerary_items_with_llm).
       → "점심 일정 삭제해줘", "카페 시간 바꿔줘" 등 세밀한 수정에 적합.
    ② patch가 적합하지 않으면 Day 전체 교체를 수행합니다 (modify_itinerary_cards_with_llm).
       → "Day 2를 애월 중심으로 바꿔줘" 등 큰 변경에 적합.
"""

import json
import os
import re
from copy import deepcopy
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv

from app_config import SUPPORTED_DESTINATION_NAME
from Graph.travel_state import (
    ItineraryDay,
    ItineraryItem,
    TravelAgentState,
    TravelCondition,
)

# ──────────────────────────────────────────────────────────────
# 환경 변수 로딩
# ──────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE_PATH = PROJECT_ROOT / ".env"

load_dotenv(dotenv_path=ENV_FILE_PATH)


# ──────────────────────────────────────────────────────────────
# 상수
# ──────────────────────────────────────────────────────────────
# 최대 허용 여행 일수. UI가 과도한 Day 버튼으로 망가지는 것을 방지합니다.
MAX_TRIP_DAY_COUNT = 31


# ══════════════════════════════════════════════════════════════
# 1. 유틸리티 함수
# ══════════════════════════════════════════════════════════════

def clamp_trip_day_count(trip_day_count: int | None) -> int | None:
    """너무 큰 Day 수가 UI를 망가뜨리지 않도록 안전 범위를 적용합니다.

    Args:
        trip_day_count: 추출된 여행 일수 (None이면 그대로 반환).

    Returns:
        int | None — 1 이상 MAX_TRIP_DAY_COUNT 이하로 클램핑된 값.
                     1 미만이면 None 반환.
    """

    if trip_day_count is None:
        return None

    if trip_day_count < 1:
        return None

    return min(trip_day_count, MAX_TRIP_DAY_COUNT)


def extract_numeric_trip_day_count(user_message: str) -> int | None:
    """LLM을 쓸 수 없을 때를 위한 최소 fallback 일수 추출입니다.

    정규식으로 명확한 숫자 패턴만 추출합니다.
    의미 판단(예: "짧은 여행" → 2~3일)은 하지 않습니다.

    지원 패턴:
        - "4박 5일" → 5 (박+1이 아니라 "일" 부분을 직접 추출)
        - "5일 여행" → 5
        - "2주 여행" → 14

    Args:
        user_message: 사용자 입력 원문.

    Returns:
        int | None — 추출된 여행 일수 (클램핑 적용). 추출 실패 시 None.
    """

    # 공백을 제거해 "4 박 5 일" 같은 변형도 매칭
    compact_user_message = user_message.replace(" ", "")

    # 패턴 1: "N박M일" — 가장 흔한 형식
    nights_days_match = re.search(r"(\d+)박(\d+)일", compact_user_message)
    if nights_days_match:
        return clamp_trip_day_count(int(nights_days_match.group(2)))

    # 패턴 2: "N일" — 단순 일수
    day_count_match = re.search(r"(\d+)일", compact_user_message)
    if day_count_match:
        return clamp_trip_day_count(int(day_count_match.group(1)))

    # 패턴 3: "N주" — 주 단위
    week_count_match = re.search(r"(\d+)주", compact_user_message)
    if week_count_match:
        return clamp_trip_day_count(int(week_count_match.group(1)) * 7)

    return None


def extract_numeric_target_day_number(
    user_message: str,
    selected_day_number: int,
) -> int:
    """LLM을 쓸 수 없을 때를 위한 최소 fallback 대상 Day 추출입니다.

    정규식으로 Day 번호를 추출하며, 7일 제한 없이 임의의 숫자를 지원합니다.

    지원 패턴:
        - "Day 12", "day12"
        - "12일차"
        - "12번째 날", "12째 날"

    Args:
        user_message:        사용자 입력 원문.
        selected_day_number: 추출 실패 시 반환할 기본값 (현재 선택된 Day).

    Returns:
        int — 추출된 Day 번호, 또는 selected_day_number.
    """

    day_patterns = [
        r"[Dd]ay\s*(\d+)",      # Day 12, day12
        r"(\d+)일차",            # 12일차
        r"(\d+)번째날",          # 12번째날 (공백 제거 후)
        r"(\d+)번째\s*날",       # 12번째 날 (공백 포함)
        r"(\d+)째날",            # 12째날
        r"(\d+)째\s*날",         # 12째 날
    ]

    compact_user_message = user_message.replace(" ", "")

    for day_pattern in day_patterns:
        day_match = re.search(day_pattern, compact_user_message)
        if day_match:
            return int(day_match.group(1))

    return selected_day_number


def build_empty_itinerary_days(trip_day_count: int) -> list[ItineraryDay]:
    """총 여행 일수에 맞춰 빈 Day 일정을 생성합니다.

    LLM 생성 전 Day 프레임을 미리 만들 때 사용합니다.

    Args:
        trip_day_count: 생성할 Day 수.

    Returns:
        list[ItineraryDay] — items가 빈 Day 목록.
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


def create_itinerary_item(
    day_number: int,
    item_index: int,
    time: str,
    title: str,
    description: str,
    travel_time: str,
    source: str = "llm",
) -> ItineraryItem:
    """LLM structured output을 UI 카드용 State 데이터로 변환합니다.

    item_id는 "day{N}-{인덱스:03d}" 형식으로 고유하게 생성합니다.

    Args:
        day_number:  소속 Day 번호.
        item_index:  Day 내 순서 번호 (1부터).
        time:        일정 시간 문자열 (예: "10:00").
        title:       카드 제목 (예: "성산일출봉").
        description: 카드 설명.
        travel_time: 이전 일정에서의 이동 시간.
        source:      생성 출처 (기본: "llm").

    Returns:
        ItineraryItem — UI 카드에 바로 사용 가능한 딕셔너리.
    """

    return {
        "item_id": f"day{day_number}-{item_index:03d}",
        "time": time,
        "title": title,
        "description": description,
        "travel_time": travel_time,
        "is_fixed": False,   # 최초 생성 시 항상 고정 해제 상태
        "source": source,
    }


def build_travel_condition_summary(
    travel_conditions: list[TravelCondition],
) -> str:
    """State에 저장된 여행 조건을 LLM 입력용 요약 문자열로 변환합니다.

    각 조건의 label을 쉼표로 연결합니다.
    예: "부모님 동반, 렌터카, 4박 5일 여행"

    Args:
        travel_conditions: 여행 조건 목록.

    Returns:
        str — 쉼표로 구분된 조건 요약, 또는 기본 안내 문구.
    """

    condition_labels = [
        travel_condition["label"]
        for travel_condition in travel_conditions
        if travel_condition.get("label")
    ]

    if not condition_labels:
        return "아직 구체적인 여행 조건이 없습니다."

    return ", ".join(condition_labels)


def build_itinerary_item_selection_summary(
    itinerary_day: ItineraryDay,
) -> str:
    """LLM이 target_item_id를 정확히 고를 수 있도록 Day item 목록을 요약합니다.

    카드 단위 patch(patch_itinerary_items_with_llm)에서 사용됩니다.
    LLM 프롬프트에 이 요약을 포함해, 기존 item_id를 정확히 참조하게 합니다.

    출력 예:
        [1] item_id=day1-001 / time=10:00 / title=성산일출봉 / ... / fixed=False
        [2] item_id=day1-002 / time=12:00 / title=점심 식당 / ... / fixed=True

    Args:
        itinerary_day: 요약할 Day 데이터.

    Returns:
        str — 줄바꿈으로 구분된 item 요약 문자열.
    """

    schedule_items = itinerary_day.get("items", [])

    if not schedule_items:
        return "선택 가능한 일정 item이 없습니다."

    summary_lines: list[str] = []

    for item_index, schedule_item in enumerate(schedule_items, start=1):
        fixed_label = "fixed=True" if schedule_item.get("is_fixed") else "fixed=False"

        summary_lines.append(
            (
                f"[{item_index}] "
                f"item_id={schedule_item.get('item_id')} / "
                f"time={schedule_item.get('time')} / "
                f"title={schedule_item.get('title')} / "
                f"description={schedule_item.get('description')} / "
                f"travel_time={schedule_item.get('travel_time')} / "
                f"{fixed_label}"
            )
        )

    return "\n".join(summary_lines)


def create_travel_condition(
    category: str,
    label: str,
    raw_text: str,
    confidence: float = 1.0,
) -> TravelCondition:
    """UI 칩으로 표시할 여행 조건 객체를 만듭니다.

    Args:
        category:   조건 분류 (예: "companion", "transport").
        label:      UI 칩 라벨 (예: "부모님 동반").
        raw_text:   사용자 원문 근거.
        confidence: 신뢰도 (기본 1.0).

    Returns:
        TravelCondition — 여행 조건 딕셔너리.
    """

    return {
        "category": category,
        "label": label,
        "raw_text": raw_text,
        "confidence": confidence,
    }


def deduplicate_travel_conditions(
    travel_conditions: list[TravelCondition],
) -> list[TravelCondition]:
    """중복 조건 칩을 제거합니다.

    (category, label) 쌍을 키로 사용하여 중복을 판별합니다.
    첫 번째 등장한 조건만 유지합니다.

    Args:
        travel_conditions: 중복이 포함될 수 있는 조건 목록.

    Returns:
        list[TravelCondition] — 중복이 제거된 조건 목록.
    """

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
    """기존 조건과 새로 추출한 조건을 병합합니다.

    단순 연결(concat) 후 중복 제거를 수행합니다.
    기존 조건이 먼저 오므로, 동일 조건이면 기존 것이 유지됩니다.

    Args:
        existing_conditions: 이미 State에 있는 조건 목록.
        new_conditions:      새로 추출한 조건 목록.

    Returns:
        list[TravelCondition] — 병합·중복 제거된 조건 목록.
    """

    return deduplicate_travel_conditions(
        existing_conditions + new_conditions
    )


# ══════════════════════════════════════════════════════════════
# 2. Fallback 해석 (LLM 없이 동작)
# ══════════════════════════════════════════════════════════════

def fallback_interpret_user_request(
    state: TravelAgentState,
) -> dict[str, object]:
    """LLM을 사용할 수 없을 때 앱이 죽지 않도록 최소 해석을 수행합니다.

    이 fallback은 의미 판단을 하지 않습니다.
    명확한 숫자 기간과 Day 번호만 추출하고,
    나머지는 사용자 요청 원문을 하나의 raw_request 조건으로 보관합니다.

    Args:
        state: 현재 LangGraph 상태.

    Returns:
        dict — user_intent, target_day_number, travel_conditions,
               (선택적) trip_day_count를 포함하는 부분 상태 업데이트.
    """

    user_message = state["user_message"]
    selected_day_number = state["selected_day_number"]

    # 숫자 기반 여행 일수 추출 (예: "4박 5일" → 5)
    trip_day_count = extract_numeric_trip_day_count(user_message)

    # 숫자 기반 대상 Day 추출 (예: "Day 3" → 3)
    target_day_number = extract_numeric_target_day_number(
        user_message=user_message,
        selected_day_number=selected_day_number,
    )

    # 기존 조건 복사 (원본 변경 방지)
    travel_conditions = list(state.get("travel_conditions", []))

    # 여행 일수가 추출되면 duration 조건 추가
    if trip_day_count is not None:
        travel_conditions = merge_travel_conditions(
            existing_conditions=travel_conditions,
            new_conditions=[
                create_travel_condition(
                    category="duration",
                    label=f"{trip_day_count}일 여행",
                    raw_text=user_message,
                    confidence=0.7,  # fallback이므로 신뢰도 낮음
                )
            ],
        )

    # 사용자 원문을 raw_request 조건으로 보관 (최대 24자)
    if user_message:
        travel_conditions = merge_travel_conditions(
            existing_conditions=travel_conditions,
            new_conditions=[
                create_travel_condition(
                    category="raw_request",
                    label=user_message[:24],   # UI 칩이 너무 길어지지 않도록 절단
                    raw_text=user_message,
                    confidence=0.4,            # raw이므로 낮은 신뢰도
                )
            ],
        )

    # 결과 조립
    result: dict[str, object] = {
        "user_intent": "create_initial_trip"
        if trip_day_count is not None
        else "general_question",
        "target_day_number": target_day_number,
        "travel_conditions": travel_conditions,
    }

    if trip_day_count is not None:
        result["trip_day_count"] = trip_day_count

    return result


# ══════════════════════════════════════════════════════════════
# 3. LLM 기반 사용자 요청 해석
# ══════════════════════════════════════════════════════════════

def interpret_user_request_with_llm(
    state: TravelAgentState,
) -> dict[str, object] | None:
    """LLM을 사용해 사용자 요청을 자유 구조로 해석합니다.

    핵심 설계 원칙:
        - 여행지, 동행자, 교통수단, 숙소 등의 후보 목록을 코드에 하드코딩하지 않습니다.
        - LLM이 사용자 문장의 의미 단위를 자유롭게 추출합니다.
        - category는 내부 분류일 뿐이고, UI에는 label을 표시합니다.
        - Day 번호는 7일 제한 없이 숫자로 추출합니다.

    Args:
        state: 현재 LangGraph 상태.

    Returns:
        dict | None — 해석 성공 시 부분 상태 업데이트.
                      실패(API 키 없음, Import 실패, 호출 예외) 시 None → fallback으로 전환.
    """

    # API 키가 없으면 LLM 해석 불가 → None 반환 → fallback
    if not os.getenv("OPENAI_API_KEY"):
        return None

    # 지연 임포트 — 패키지 미설치 시 앱 전체가 죽지 않도록 방어
    try:
        from langchain_openai import ChatOpenAI
        from pydantic import BaseModel, Field
    except ImportError:
        return None

    # ── Pydantic Structured Output 스키마 ────────────────────
    # LLM 응답을 강제로 이 구조에 맞추게 합니다.

    class TravelConditionExtraction(BaseModel):
        """개별 여행 조건 추출 결과."""

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
        """사용자 요청 전체 해석 결과."""

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

    # ── 현재 앱 상태를 LLM에 전달 ────────────────────────────
    current_context = {
        "selected_day_number": state.get("selected_day_number"),
        "destination_name": state.get("destination_name"),
        "trip_day_count": state.get("trip_day_count"),
        "travel_conditions": state.get("travel_conditions", []),
        "itinerary_days_count": len(state.get("itinerary_days", [])),
    }

    # ── 시스템 프롬프트 ──────────────────────────────────────
    # 핵심: "후보 목록에 묶이지 마라"를 반복 강조합니다.
    # LLM이 훈련 데이터에 있는 고정 분류에 빠지지 않도록 유도합니다.
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

    # ── LLM 호출 ─────────────────────────────────────────────
    model_name = os.getenv("TRAVEL_AGENT_MODEL", "gpt-4o-mini")

    chat_model = ChatOpenAI(
        model=model_name,
        temperature=0,  # 구조화 해석이므로 결정적 출력
    )

    structured_model = chat_model.with_structured_output(
        TravelRequestInterpretation
    )

    try:
        interpretation = structured_model.invoke(
            [
                ("system", system_prompt),
                ("human", user_prompt),
            ]
        )
    except Exception:
        return None  # LLM 호출 실패 → fallback으로 전환

    # ── 해석 결과를 State 업데이트용 딕셔너리로 변환 ──────────

    # 새로 추출된 조건 목록 구성
    new_conditions: list[TravelCondition] = []

    # 여행지가 제주로 감지되면 destination 조건 추가
    if interpretation.destination_name == SUPPORTED_DESTINATION_NAME:
        new_conditions.append(
            create_travel_condition(
                category="destination",
                label=f"{SUPPORTED_DESTINATION_NAME} 여행",
                raw_text=interpretation.destination_name,
                confidence=1.0,
            )
        )

    # 여행 일수가 감지되면 duration 조건 추가
    if interpretation.trip_day_count is not None:
        duration_label = (
            interpretation.trip_duration_label               # LLM이 추출한 원문 라벨 우선
            or f"{interpretation.trip_day_count}일 여행"      # 없으면 숫자 기반 생성
        )

        new_conditions.append(
            create_travel_condition(
                category="duration",
                label=duration_label,
                raw_text=duration_label,
                confidence=1.0,
            )
        )

    # LLM이 추출한 개별 조건들 추가
    for condition in interpretation.travel_conditions:
        new_conditions.append(
            create_travel_condition(
                category=condition.category,
                label=condition.label,
                raw_text=condition.raw_text,
                confidence=condition.confidence,
            )
        )

    # 기존 조건과 병합
    existing_conditions = list(state.get("travel_conditions", []))
    merged_conditions = merge_travel_conditions(
        existing_conditions=existing_conditions,
        new_conditions=new_conditions,
    )

    # 결과 딕셔너리 조립
    result: dict[str, object] = {
        "user_intent": interpretation.user_intent,
        "destination_name": SUPPORTED_DESTINATION_NAME,  # 제주 고정
        "travel_conditions": merged_conditions,
        "agent_response": interpretation.agent_response,
    }

    # destination_name이 있어도 항상 제주로 덮어쓰기 (제주 전용 앱)
    if interpretation.destination_name:
        result["destination_name"] = SUPPORTED_DESTINATION_NAME

    # 여행 일수 (클램핑 적용)
    trip_day_count = clamp_trip_day_count(interpretation.trip_day_count)
    if trip_day_count is not None:
        result["trip_day_count"] = trip_day_count

    # 대상 Day 번호 — LLM 결과 우선, 없으면 정규식 fallback
    if interpretation.target_day_number is not None:
        result["target_day_number"] = interpretation.target_day_number
    else:
        result["target_day_number"] = extract_numeric_target_day_number(
            user_message=state["user_message"],
            selected_day_number=state["selected_day_number"],
        )

    return result


# ══════════════════════════════════════════════════════════════
# 4. 일정 유효성 검사 및 조회 유틸리티
# ══════════════════════════════════════════════════════════════

def validate_generated_itinerary_days(
    itinerary_days: list[ItineraryDay],
    trip_day_count: int,
) -> bool:
    """LLM이 생성한 일정 카드 데이터가 UI에 넣어도 안전한지 검사합니다.

    검사 항목:
        1. Day 개수가 trip_day_count와 일치하는가
        2. Day 번호가 1~trip_day_count까지 빠짐없이 존재하는가
        3. 각 Day에 최소 1개 이상의 item이 있는가
        4. 각 item에 필수 필드가 모두 존재하는가
        5. title과 time이 비어 있지 않은가

    Args:
        itinerary_days: 검사할 일정 데이터.
        trip_day_count: 기대하는 총 Day 수.

    Returns:
        bool — 모든 검사를 통과하면 True.
    """

    if len(itinerary_days) != trip_day_count:
        return False

    expected_day_numbers = set(range(1, trip_day_count + 1))
    actual_day_numbers = {
        itinerary_day["day_number"]
        for itinerary_day in itinerary_days
    }

    if actual_day_numbers != expected_day_numbers:
        return False

    for itinerary_day in itinerary_days:
        schedule_items = itinerary_day.get("items", [])

        if not schedule_items:
            return False

        for schedule_item in schedule_items:
            required_fields = [
                "item_id",
                "time",
                "title",
                "description",
                "travel_time",
                "is_fixed",
                "source",
            ]

            for required_field in required_fields:
                if required_field not in schedule_item:
                    return False

            if not schedule_item["title"].strip():
                return False

            if not schedule_item["time"].strip():
                return False

    return True


def has_existing_itinerary_items(
    itinerary_days: list[ItineraryDay],
) -> bool:
    """기존 일정 안에 실제 카드 item이 있는지 확인합니다.

    빈 Day 프레임만 있고 item이 없는 경우를 구분하는 데 사용합니다.

    Args:
        itinerary_days: 전체 일정 데이터.

    Returns:
        bool — 하나라도 item이 있으면 True.
    """

    return any(
        bool(itinerary_day.get("items"))
        for itinerary_day in itinerary_days
    )


def find_itinerary_day_by_number(
    itinerary_days: list[ItineraryDay],
    day_number: int,
) -> ItineraryDay | None:
    """Day 번호로 기존 일정 Day를 찾습니다.

    Args:
        itinerary_days: 전체 일정 데이터.
        day_number:     찾을 Day 번호.

    Returns:
        ItineraryDay | None — 해당 Day, 또는 None.
    """

    for itinerary_day in itinerary_days:
        if itinerary_day["day_number"] == day_number:
            return itinerary_day

    return None


def resolve_target_day_number_for_modification(
    state: TravelAgentState,
) -> int:
    """자연어 수정 대상 Day를 결정합니다.

    우선순위:
        1. LLM 분석 결과의 target_day_number (양의 정수일 때만)
        2. 현재 UI에서 선택된 selected_day_number

    Args:
        state: 현재 LangGraph 상태.

    Returns:
        int — 수정 대상 Day 번호.
    """

    target_day_number = state.get("target_day_number")

    if isinstance(target_day_number, int) and target_day_number > 0:
        return target_day_number

    return state["selected_day_number"]


def get_fixed_items_from_day(
    itinerary_day: ItineraryDay,
) -> list[ItineraryItem]:
    """수정 중에도 유지해야 하는 고정 카드 목록을 가져옵니다.

    deepcopy를 사용해 원본을 훼손하지 않습니다.

    Args:
        itinerary_day: 대상 Day 데이터.

    Returns:
        list[ItineraryItem] — 고정된 item의 깊은 복사 목록.
    """

    return [
        deepcopy(schedule_item)
        for schedule_item in itinerary_day.get("items", [])
        if schedule_item.get("is_fixed")
    ]


# ══════════════════════════════════════════════════════════════
# 5. 수정 전용 유틸리티
# ══════════════════════════════════════════════════════════════

def create_modified_itinerary_item(
    day_number: int,
    item_index: int,
    time: str,
    title: str,
    description: str,
    travel_time: str,
) -> ItineraryItem:
    """LLM이 만든 수정 결과를 UI 카드용 item으로 변환합니다.

    item_id에 "modified"를 포함시켜 원본과 구분합니다.

    Args:
        day_number:  소속 Day 번호.
        item_index:  Day 내 순서 번호 (1부터).
        time:        수정된 시간.
        title:       수정된 제목.
        description: 수정된 설명.
        travel_time: 수정된 이동 시간.

    Returns:
        ItineraryItem — 수정된 item 딕셔너리.
    """

    return {
        "item_id": f"day{day_number}-modified-{item_index:03d}",
        "time": time,
        "title": title,
        "description": description,
        "travel_time": travel_time,
        "is_fixed": False,
        "source": "llm",
    }


def create_patch_item_id(
    day_number: int,
    existing_items: list[ItineraryItem],
) -> str:
    """기존 item_id와 충돌하지 않는 patch item_id를 만듭니다.

    add_item 패치 시 새 item에 고유 ID를 부여하는 데 사용합니다.
    기존 ID 목록을 확인하며 충돌이 없을 때까지 인덱스를 증가시킵니다.

    Args:
        day_number:     소속 Day 번호.
        existing_items: 현재 Day의 item 목록.

    Returns:
        str — 충돌 없는 새 item_id (예: "day1-patch-006").
    """

    existing_item_ids = {
        str(item.get("item_id"))
        for item in existing_items
    }

    item_index = len(existing_items) + 1

    while True:
        candidate_item_id = f"day{day_number}-patch-{item_index:03d}"

        if candidate_item_id not in existing_item_ids:
            return candidate_item_id

        item_index += 1


def build_existing_item_lookup(
    existing_items: list[ItineraryItem],
) -> dict[str, ItineraryItem]:
    """기존 item을 item_id 기준으로 O(1) 조회할 수 있게 변환합니다.

    Args:
        existing_items: 기존 item 목록.

    Returns:
        dict — item_id → ItineraryItem 매핑.
    """

    return {
        str(item.get("item_id")): item
        for item in existing_items
        if item.get("item_id")
    }


# ══════════════════════════════════════════════════════════════
# 6. 카드 단위 Patch 유효성 검사
# ══════════════════════════════════════════════════════════════

def validate_item_patch_operation(
    existing_items: list[ItineraryItem],
    patch_operation: dict,
) -> bool:
    """카드 단위 patch operation 하나가 안전한지 검사합니다.

    검사 규칙:
        - action이 허용된 4개 중 하나인가
        - add_item은 title과 time이 필수
        - delete_item/update_item/toggle_fixed는 target_item_id가 필수
        - target_item_id가 실제 존재하는 item인가
        - 고정된(is_fixed=True) item에 delete/update를 시도하지 않는가
        - update_item은 변경할 필드가 최소 1개 이상인가

    Args:
        existing_items:  현재 Day의 item 목록.
        patch_operation: 검사할 패치 명령 딕셔너리.

    Returns:
        bool — 안전하면 True, 위험하면 False.
    """

    action = patch_operation.get("action")
    target_item_id = patch_operation.get("target_item_id")
    existing_item_lookup = build_existing_item_lookup(existing_items)

    # 허용된 action 목록
    if action not in {
        "add_item",
        "delete_item",
        "update_item",
        "toggle_fixed",
    }:
        return False

    # add_item은 title, time이 필수 (새 카드 생성이므로)
    if action == "add_item":
        title = str(patch_operation.get("title", "")).strip()
        time = str(patch_operation.get("time", "")).strip()

        if not title or not time:
            return False

        return True

    # add_item 외의 action은 target_item_id가 필수
    if not target_item_id:
        return False

    # target_item_id가 실제 존재하는 item인지 확인
    target_item = existing_item_lookup.get(str(target_item_id))
    if target_item is None:
        return False

    # 고정된 item에 대한 delete/update는 차단
    if action in {"delete_item", "update_item"}:
        if target_item.get("is_fixed"):
            return False

    # update_item은 변경할 값이 최소 1개는 있어야 의미가 있음
    if action == "update_item":
        has_updatable_value = any(
            str(patch_operation.get(field_name, "")).strip()
            for field_name in [
                "time",
                "title",
                "description",
                "travel_time",
            ]
        )

        if not has_updatable_value:
            return False

    return True


def filter_valid_item_patch_operations(
    existing_items: list[ItineraryItem],
    patch_operations: list[dict],
) -> list[dict]:
    """LLM이 만든 patch 중 안전하게 적용 가능한 operation만 남깁니다.

    Args:
        existing_items:   현재 Day의 item 목록.
        patch_operations: LLM이 생성한 패치 명령 목록.

    Returns:
        list[dict] — 유효한 패치만 필터링된 목록.
    """

    return [
        patch_operation
        for patch_operation in patch_operations
        if validate_item_patch_operation(
            existing_items=existing_items,
            patch_operation=patch_operation,
        )
    ]


# ══════════════════════════════════════════════════════════════
# 7. Patch 디버깅 트레이스
# ══════════════════════════════════════════════════════════════

def is_item_patch_trace_enabled() -> bool:
    """카드 단위 patch trace 로그 출력 여부를 확인합니다.

    환경변수 TRAVEL_PATCH_TRACE=1 로 활성화합니다.

    Returns:
        bool — 트레이스 활성화 여부.
    """

    return os.getenv("TRAVEL_PATCH_TRACE", "0") == "1"


def print_item_patch_trace(
    label: str,
    payload: object,
) -> None:
    """카드 단위 patch 디버깅용 trace 로그를 출력합니다.

    TRAVEL_PATCH_TRACE=1일 때만 동작합니다.
    JSON 직렬화가 가능하면 보기 좋게 출력하고, 불가능하면 그대로 출력합니다.

    Args:
        label:   로그 구분 라벨 (예: "raw_patch_operations").
        payload: 출력할 데이터.
    """

    if not is_item_patch_trace_enabled():
        return

    print(f"\n[ITEM_PATCH_TRACE] {label}")

    try:
        print(
            json.dumps(
                payload,
                ensure_ascii=False,  # 한국어 유니코드 그대로 출력
                indent=2,
            )
        )
    except TypeError:
        print(payload)


def validate_item_patch_operations_atomically(
    existing_items: list[ItineraryItem],
    patch_operations: list[dict],
) -> list[dict] | None:
    """patch operations 전체가 안전할 때만 그대로 반환합니다.

    원자적(atomic) 검증: 하나라도 안전하지 않은 operation이 있으면
    전체 patch를 취소(None 반환)합니다.
    부분 적용은 의도치 않은 상태를 만들 수 있으므로 all-or-nothing 전략입니다.

    Args:
        existing_items:   현재 Day의 item 목록.
        patch_operations: 검증할 패치 명령 목록.

    Returns:
        list[dict] | None — 전체 유효하면 원본 그대로, 하나라도 무효하면 None.
    """

    if not patch_operations:
        return None

    valid_patch_operations = filter_valid_item_patch_operations(
        existing_items=existing_items,
        patch_operations=patch_operations,
    )

    # 유효한 패치 수가 원본과 다르면 → 일부가 무효 → 전체 취소
    if len(valid_patch_operations) != len(patch_operations):
        return None

    return valid_patch_operations


def create_item_patch_failure_result(
    existing_itinerary_days: list[ItineraryDay],
) -> dict[str, object]:
    """카드 단위 patch 실패 시 기존 일정을 유지한 채 실패 응답을 반환합니다.

    deepcopy로 기존 데이터를 보존하여, 실패해도 State가 오염되지 않습니다.

    Args:
        existing_itinerary_days: 현재 전체 일정 데이터.

    Returns:
        dict — 기존 itinerary_days + 안내 agent_response.
    """

    return {
        "itinerary_days": deepcopy(existing_itinerary_days),
        "agent_response": (
            "수정할 일정 카드를 정확히 찾지 못했습니다. "
            "예를 들어 '둘째 날 점심 일정 삭제해줘'처럼 "
            "수정할 Day와 대상 일정을 조금 더 구체적으로 입력해 주세요."
        ),
    }


# ══════════════════════════════════════════════════════════════
# 8. 시간 파싱 및 정렬
# ══════════════════════════════════════════════════════════════

def parse_schedule_time_to_minutes(time_text: str) -> int | None:
    """일정 시간 문자열을 정렬 가능한 분 단위 값으로 변환합니다.

    지원 형식:
        - "09:30" → 570
        - "9:30"  → 570
        - "오전 9:30" → 570
        - "오후 1:00" → 780
        - "14시" → 840

    Args:
        time_text: 파싱할 시간 문자열.

    Returns:
        int | None — 0시 0분 기준 분 단위 값. 파싱 실패 시 None.
    """

    normalized_time_text = time_text.strip()

    if not normalized_time_text:
        return None

    # 오전/오후 처리
    meridiem_offset = 0

    if "오후" in normalized_time_text:
        meridiem_offset = 12
        normalized_time_text = normalized_time_text.replace("오후", "").strip()
    elif "오전" in normalized_time_text:
        normalized_time_text = normalized_time_text.replace("오전", "").strip()

    # "HH:MM" 또는 "HH시MM분" 패턴 매칭
    time_match = re.search(
        r"(\d{1,2})\s*[:시]\s*(\d{1,2})?",
        normalized_time_text,
    )

    if time_match is None:
        return None

    hour = int(time_match.group(1))
    minute_text = time_match.group(2)
    minute = int(minute_text) if minute_text is not None else 0

    # 분 범위 검증
    if minute < 0 or minute >= 60:
        return None

    # 오후 보정: "오후 1시" → 13시, "오후 12시" → 12시(그대로)
    if meridiem_offset == 12 and hour < 12:
        hour += 12

    # 오전 12시 → 0시 (자정)
    if meridiem_offset == 0 and "오전" in time_text and hour == 12:
        hour = 0

    # 시 범위 검증
    if hour < 0 or hour >= 24:
        return None

    return hour * 60 + minute


def sort_itinerary_items_by_time(
    itinerary_items: list[ItineraryItem],
) -> list[ItineraryItem]:
    """일정 item을 time 기준으로 정렬합니다.

    정렬 전략:
        - time을 파싱할 수 있는 item → 시간순 정렬
        - time을 파싱할 수 없는 item → 기존 상대 순서를 유지한 채 뒤에 배치

    정렬 키: (파싱 가능 여부, 분 값 또는 원래 인덱스, 원래 인덱스)
    → 안정 정렬(stable sort)로 동률일 때 원래 순서 유지

    Args:
        itinerary_items: 정렬할 item 목록.

    Returns:
        list[ItineraryItem] — 시간순으로 정렬된 item 목록.
    """

    # (원래 인덱스, item) 쌍으로 래핑
    indexed_items = list(enumerate(itinerary_items))

    def get_sort_key(indexed_item: tuple[int, ItineraryItem]) -> tuple[int, int, int]:
        original_index, itinerary_item = indexed_item
        parsed_minutes = parse_schedule_time_to_minutes(
            str(itinerary_item.get("time", ""))
        )

        if parsed_minutes is None:
            # 파싱 불가 → (1, ...) 로 뒤쪽 배치
            return (1, original_index, original_index)

        # 파싱 가능 → (0, 분값, ...) 로 시간순 배치
        return (0, parsed_minutes, original_index)

    return [
        itinerary_item
        for _, itinerary_item in sorted(indexed_items, key=get_sort_key)
    ]


# ══════════════════════════════════════════════════════════════
# 9. Day 병합 유틸리티
# ══════════════════════════════════════════════════════════════

def merge_replacement_items_with_fixed_items(
    existing_day: ItineraryDay,
    replacement_items: list[ItineraryItem],
) -> ItineraryDay:
    """기존 Day에서 fixed item은 보존하고 나머지만 교체합니다.

    고정 item은 원래 위치에 유지하고, 비고정 item 자리에 replacement를 순서대로 채웁니다.
    병합 후 시간순 정렬을 적용합니다.

    Args:
        existing_day:      원본 Day 데이터.
        replacement_items: 비고정 item을 대체할 새 item 목록.

    Returns:
        ItineraryDay — 병합된 새 Day 데이터.
    """

    merged_items: list[ItineraryItem] = []
    replacement_item_index = 0

    for existing_item in existing_day.get("items", []):
        if existing_item.get("is_fixed"):
            # 고정 item은 deepcopy로 보존
            merged_items.append(deepcopy(existing_item))
            continue

        # 비고정 item → replacement로 교체
        if replacement_item_index < len(replacement_items):
            merged_items.append(replacement_items[replacement_item_index])
            replacement_item_index += 1

    # replacement가 더 남아 있으면 뒤에 추가
    while replacement_item_index < len(replacement_items):
        merged_items.append(replacement_items[replacement_item_index])
        replacement_item_index += 1

    # 시간순 정렬 적용
    sorted_items = sort_itinerary_items_by_time(merged_items)

    return {
        "day_number": existing_day["day_number"],
        "title": existing_day.get("title", f"Day {existing_day['day_number']}"),
        "items": sorted_items,
    }


def merge_modified_day_into_itinerary(
    existing_itinerary_days: list[ItineraryDay],
    modified_day: ItineraryDay,
) -> list[ItineraryDay]:
    """수정된 Day 하나를 전체 itinerary_days에 병합합니다.

    수정된 Day만 교체하고, 나머지 Day는 deepcopy로 원본을 보존합니다.

    Args:
        existing_itinerary_days: 기존 전체 일정.
        modified_day:            교체할 수정된 Day.

    Returns:
        list[ItineraryDay] — 병합된 새 전체 일정.
    """

    merged_itinerary_days: list[ItineraryDay] = []

    for itinerary_day in existing_itinerary_days:
        if itinerary_day["day_number"] == modified_day["day_number"]:
            merged_itinerary_days.append(modified_day)
        else:
            merged_itinerary_days.append(deepcopy(itinerary_day))

    return merged_itinerary_days


# ══════════════════════════════════════════════════════════════
# 10. Patch Operation 적용
# ══════════════════════════════════════════════════════════════

def apply_item_patch_operations(
    existing_day: ItineraryDay,
    patch_operations: list[dict],
) -> ItineraryDay:
    """LLM이 만든 카드 단위 patch operations를 기존 Day에 적용합니다.

    지원되는 action:
        - add_item:     새 카드 추가
        - delete_item:  기존 카드 삭제 (고정 카드는 건너뜀)
        - update_item:  기존 카드의 필드 부분 수정 (고정 카드는 건너뜀)
        - toggle_fixed: 카드의 고정 상태 변경

    적용 후 시간순 정렬을 수행합니다.

    Args:
        existing_day:     원본 Day 데이터.
        patch_operations: 적용할 패치 명령 목록.

    Returns:
        ItineraryDay — 패치 적용 후의 새 Day 데이터.
    """

    day_number = existing_day["day_number"]
    patched_items = deepcopy(existing_day.get("items", []))  # 원본 보호

    for patch_operation in patch_operations:
        action = patch_operation.get("action")
        target_item_id = patch_operation.get("target_item_id")

        # ── add_item: 새 카드 추가 ───────────────────────────
        if action == "add_item":
            patched_items.append(
                {
                    "item_id": create_patch_item_id(
                        day_number=day_number,
                        existing_items=patched_items,
                    ),
                    "time": patch_operation.get("time", "시간 미정"),
                    "title": patch_operation.get("title", "일정 미정"),
                    "description": patch_operation.get("description", ""),
                    "travel_time": patch_operation.get(
                        "travel_time",
                        "이동 미정",
                    ),
                    "is_fixed": False,
                    "source": "llm_patch",
                }
            )
            continue

        # target_item_id가 없으면 건너뜀
        if not target_item_id:
            continue

        # 해당 item을 찾아 action 적용
        for item_index, patched_item in enumerate(patched_items):
            if patched_item.get("item_id") != target_item_id:
                continue

            # ── toggle_fixed: 고정 상태 변경 ─────────────────
            if action == "toggle_fixed":
                requested_fixed_value = patch_operation.get("is_fixed")

                if requested_fixed_value is None:
                    requested_fixed_value = True

                patched_item["is_fixed"] = bool(requested_fixed_value)
                break

            # 고정된 item에 대한 delete/update는 무시
            if patched_item.get("is_fixed"):
                break

            # ── delete_item: 카드 삭제 ───────────────────────
            if action == "delete_item":
                patched_items.pop(item_index)
                break

            # ── update_item: 카드 필드 부분 수정 ─────────────
            if action == "update_item":
                for field_name in [
                    "time",
                    "title",
                    "description",
                    "travel_time",
                ]:
                    new_value = patch_operation.get(field_name)

                    # 비어 있지 않은 값만 반영
                    if new_value is not None and str(new_value).strip():
                        patched_item[field_name] = new_value

                patched_item["source"] = "llm_patch"
                break

    return {
        "day_number": existing_day["day_number"],
        "title": existing_day.get("title", f"Day {day_number}"),
        "items": sort_itinerary_items_by_time(patched_items),
    }


# ══════════════════════════════════════════════════════════════
# 11. LLM 기반 일정 최초 생성
# ══════════════════════════════════════════════════════════════

def generate_itinerary_cards_with_llm(
    state: TravelAgentState,
) -> dict[str, object] | None:
    """LLM structured output으로 Day별 일정 카드 데이터를 생성합니다.

    여행 일정을 처음 만들 때 호출됩니다.
    LLM에게 trip_day_count일치의 일정을 한 번에 생성하도록 요청합니다.

    Args:
        state: 현재 LangGraph 상태.

    Returns:
        dict | None — 생성 성공 시 itinerary_days + agent_response.
                      실패 시 None.
    """

    if not os.getenv("OPENAI_API_KEY"):
        return None

    try:
        from langchain_openai import ChatOpenAI
        from pydantic import BaseModel, Field
    except ImportError:
        return None

    # ── Pydantic Structured Output 스키마 ────────────────────
    class ItineraryItemOutput(BaseModel):
        """개별 일정 item 생성 결과."""

        time: str = Field(description="일정 시간. 예: 10:00, 13:30")
        title: str = Field(description="UI 카드에 표시할 짧은 일정 제목")
        description: str = Field(description="사용자 조건을 반영한 짧은 설명")
        travel_time: str = Field(description="이전 일정에서 이 일정까지의 대략적인 이동 시간")

    class ItineraryDayOutput(BaseModel):
        """Day 단위 생성 결과."""

        day_number: int = Field(description="Day 번호. 1부터 시작합니다.")
        title: str = Field(description="Day 제목. 예: Day 1")
        items: list[ItineraryItemOutput] = Field(description="해당 Day의 일정 카드 목록")

    class ItineraryGenerationOutput(BaseModel):
        """전체 생성 결과."""

        itinerary_days: list[ItineraryDayOutput] = Field(description="전체 Day별 일정 카드 데이터")
        agent_response: str = Field(description="사용자에게 보여줄 짧은 한국어 응답")

    trip_day_count = state.get("trip_day_count")

    if trip_day_count is None:
        return None

    travel_condition_summary = build_travel_condition_summary(
        state.get("travel_conditions", [])
    )

    # ── 시스템 프롬프트 ──────────────────────────────────────
    # 14개 규칙으로 LLM 출력을 세밀하게 제어합니다.
    # 특히 "코드에 저장된 샘플 일정이 있다고 가정하지 마라"를 강조하여
    # LLM이 학습 데이터의 고정 일정을 복사하는 것을 방지합니다.
    system_prompt = f"""
너는 제주 여행 플래너 앱의 일정 카드 생성 노드다.

현재 앱은 제주 여행만 지원한다.
너는 사용자의 자연어 요청과 State에 저장된 여행 조건을 바탕으로
UI가 바로 표시할 수 있는 Day별 일정 카드 데이터를 생성해야 한다.

중요 규칙:
1. 코드에 저장된 샘플 일정이나 고정 장소 목록이 있다고 가정하지 마라.
2. 사용자의 자연어 조건과 현재 State만 근거로 일정을 만든다.
3. 총 {trip_day_count}일 일정을 생성한다.
4. Day 번호는 반드시 1부터 {trip_day_count}까지 빠짐없이 생성한다.
5. 각 Day에는 3개에서 5개의 일정 item을 만든다.
6. 사용자 조건을 반드시 반영한다.
   예: 동행자, 이동 방식, 숙소 조건, 걷는 거리, 여행 분위기, 음식 선호, 예산, 접근성.
7. 하루 동선이 과도하게 흩어지지 않도록 같은 권역 중심으로 구성한다.
8. time은 UI에 표시 가능한 짧은 시간 문자열로 작성한다.
9. title은 카드 제목으로 짧고 명확하게 작성한다.
10. description은 이 일정이 사용자 조건에 맞는 이유를 짧게 설명한다.
11. travel_time은 이전 일정에서의 대략적인 이동 시간으로 작성한다.
12. 실제 지도 API 검증 전이므로 주소, 위도, 경도, place_id는 만들지 않는다.
13. 제주 외 지역 일정은 절대 생성하지 않는다.
14. 반환 형식은 structured output schema를 반드시 따른다.
"""

    user_prompt = f"""
현재 State:
destination_name: {state.get("destination_name")}
trip_day_count: {trip_day_count}
selected_day_number: {state.get("selected_day_number")}
travel_conditions: {travel_condition_summary}
existing_itinerary_days: {state.get("itinerary_days", [])}

사용자 입력:
{state.get("user_message")}
"""

    chat_model = ChatOpenAI(
        model=os.getenv("TRAVEL_AGENT_MODEL", "gpt-4o-mini"),
        temperature=0,
    )

    structured_model = chat_model.with_structured_output(
        ItineraryGenerationOutput
    )

    try:
        generation_result = structured_model.invoke(
            [
                ("system", system_prompt),
                ("human", user_prompt),
            ]
        )
    except Exception:
        return None

    # ── LLM 출력을 내부 State 형식으로 변환 ──────────────────
    itinerary_days: list[ItineraryDay] = []

    for day_output in generation_result.itinerary_days:
        items: list[ItineraryItem] = []

        for item_index, item_output in enumerate(day_output.items, start=1):
            items.append(
                create_itinerary_item(
                    day_number=day_output.day_number,
                    item_index=item_index,
                    time=item_output.time,
                    title=item_output.title,
                    description=item_output.description,
                    travel_time=item_output.travel_time,
                    source="llm",
                )
            )

        itinerary_days.append(
            {
                "day_number": day_output.day_number,
                "title": day_output.title or f"Day {day_output.day_number}",
                "items": sort_itinerary_items_by_time(items),
            }
        )

    # ── 생성 결과 유효성 검사 ────────────────────────────────
    if not validate_generated_itinerary_days(
        itinerary_days=itinerary_days,
        trip_day_count=trip_day_count,
    ):
        return None

    return {
        "itinerary_days": itinerary_days,
        "agent_response": generation_result.agent_response,
    }


# ══════════════════════════════════════════════════════════════
# 12. LLM 기반 카드 단위 Patch
# ══════════════════════════════════════════════════════════════

def patch_itinerary_items_with_llm(
    state: TravelAgentState,
) -> dict[str, object] | None:
    """자연어 요청을 카드 단위 patch operation으로 변환해 적용합니다.

    일정 수정의 1차 시도입니다.
    "점심 일정 삭제해줘", "카페 추가해줘" 같은 세밀한 수정에 적합합니다.

    LLM이 can_apply_as_item_patch=False를 반환하면 None을 반환하여,
    상위 함수가 Day 전체 교체(modify_itinerary_cards_with_llm)로 전환합니다.

    Args:
        state: 현재 LangGraph 상태.

    Returns:
        dict | None — 패치 성공 시 itinerary_days + agent_response.
                      적합하지 않거나 실패 시 None.
    """

    if not os.getenv("OPENAI_API_KEY"):
        return None

    try:
        from langchain_openai import ChatOpenAI
        from pydantic import BaseModel, Field
    except ImportError:
        return None

    # ── Pydantic Structured Output 스키마 ────────────────────
    class ItemPatchOperationOutput(BaseModel):
        """개별 패치 명령."""

        action: Literal[
            "add_item",
            "delete_item",
            "update_item",
            "toggle_fixed",
        ] = Field(description="카드 단위 수정 작업 종류")
        target_item_id: str | None = Field(
            default=None,
            description=(
                "기존 item을 대상으로 하는 경우 정확한 item_id. "
                "add_item이면 null."
            ),
        )
        time: str | None = Field(
            default=None,
            description="add_item 또는 update_item에서 사용할 시간"
        )
        title: str | None = Field(
            default=None,
            description="add_item 또는 update_item에서 사용할 카드 제목"
        )
        description: str | None = Field(
            default=None,
            description="add_item 또는 update_item에서 사용할 설명"
        )
        travel_time: str | None = Field(
            default=None,
            description="add_item 또는 update_item에서 사용할 이동 시간"
        )
        is_fixed: bool | None = Field(
            default=None,
            description="toggle_fixed에서 사용할 고정 상태"
        )

    class ItemPatchOutput(BaseModel):
        """전체 패치 판단 결과."""

        can_apply_as_item_patch: bool = Field(
            description=(
                "요청을 카드 단위 patch로 안전하게 처리할 수 있으면 true. "
                "Day 전체 재구성이 더 맞으면 false."
            )
        )
        target_day_number: int = Field(
            description="수정 대상 Day 번호"
        )
        patch_operations: list[ItemPatchOperationOutput] = Field(
            default_factory=list,
            description="적용할 카드 단위 patch operation 목록"
        )
        agent_response: str = Field(
            description="사용자에게 보여줄 짧은 한국어 응답"
        )

    existing_itinerary_days = state.get("itinerary_days", [])
    target_day_number = resolve_target_day_number_for_modification(state)

    existing_day = find_itinerary_day_by_number(
        itinerary_days=existing_itinerary_days,
        day_number=target_day_number,
    )

    if existing_day is None:
        return None

    travel_condition_summary = build_travel_condition_summary(
        state.get("travel_conditions", [])
    )

    # 기존 item 요약 — LLM이 정확한 item_id를 참조하도록 제공
    item_selection_summary = build_itinerary_item_selection_summary(
        existing_day
    )

    # ── 시스템 프롬프트 ──────────────────────────────────────
    # 16개 규칙으로 카드 단위 patch의 안전성을 제어합니다.
    # 특히 "확실한 target_item_id를 고를 수 없으면 can_apply_as_item_patch=false"가
    # 핵심 안전장치입니다.
    system_prompt = f"""
너는 제주 여행 플래너 앱의 카드 단위 일정 수정 노드다.

현재 앱은 제주 여행만 지원한다.
너는 사용자의 자연어 요청을 기존 itinerary item에 대한 patch operation으로 변환한다.

중요 규칙:
1. 코드에 저장된 장소 후보나 샘플 일정을 가정하지 마라.
2. 사용자의 자연어 요청과 현재 State만 근거로 판단한다.
3. target_item_id는 반드시 기존 item_id 중 하나를 그대로 사용한다.
4. add_item은 target_item_id를 null로 둔다.
5. delete_item, update_item, toggle_fixed는 target_item_id가 반드시 필요하다.
6. is_fixed=True인 item은 delete_item 또는 update_item 대상으로 삼지 않는다.
7. is_fixed=True인 item은 toggle_fixed로 해제 요청을 받은 경우에만 바꿀 수 있다.
8. 요청이 "Day 전체를 애월 중심으로 바꿔줘"처럼 전체 재구성에 가까우면 can_apply_as_item_patch=false를 반환한다.
9. 요청이 특정 식사, 카페, 일정, 시간, 고정/삭제/추가처럼 카드 단위면 can_apply_as_item_patch=true를 반환한다.
10. 제주 외 지역 일정은 만들지 않는다.
11. 주소, 위도, 경도, place_id는 만들지 않는다.
12. 반환 형식은 structured output schema를 반드시 따른다.
13. 사용자가 "첫 번째", "두 번째", "마지막" 같은 순서를 말하면 item summary의 [번호]를 기준으로 target_item_id를 고른다.
14. 사용자가 "점심", "저녁", "카페", "숙소", "산책" 같은 의미를 말하면 title, description, time을 함께 보고 가장 가까운 item_id를 고른다.
15. target_item_id를 새로 만들지 말고 item summary에 있는 item_id만 사용한다.
16. 확실한 target_item_id를 고를 수 없으면 can_apply_as_item_patch=false를 반환한다.

수정 대상 Day:
Day {target_day_number}
"""

    user_prompt = f"""
현재 State 요약:
destination_name: {state.get("destination_name")}
trip_day_count: {state.get("trip_day_count")}
selected_day_number: {state.get("selected_day_number")}
target_day_number: {target_day_number}
travel_conditions: {travel_condition_summary}

수정 대상 Day의 item 선택용 요약:
{item_selection_summary}

수정 대상 Day의 원본 items:
{existing_day.get("items", [])}

사용자 자연어 요청:
{state.get("user_message")}
"""

    chat_model = ChatOpenAI(
        model=os.getenv("TRAVEL_AGENT_MODEL", "gpt-4o-mini"),
        temperature=0,
    )

    structured_model = chat_model.with_structured_output(ItemPatchOutput)

    try:
        patch_result = structured_model.invoke(
            [
                ("system", system_prompt),
                ("human", user_prompt),
            ]
        )
    except Exception:
        return None

    # LLM이 "카드 단위 patch로는 부적합"이라 판단하면 → None → Day 전체 교체로 전환
    if not patch_result.can_apply_as_item_patch:
        return None

    # Pydantic 모델을 dict로 변환 (None 필드 제외)
    patch_operations = [
        patch_operation.model_dump(exclude_none=True)
        for patch_operation in patch_result.patch_operations
    ]

    # 디버깅 트레이스 출력
    print_item_patch_trace(
        label="raw_patch_operations",
        payload=patch_operations,
    )

    # ── 원자적 유효성 검사 ───────────────────────────────────
    # 하나라도 유효하지 않으면 전체 취소
    valid_patch_operations = validate_item_patch_operations_atomically(
        existing_items=existing_day.get("items", []),
        patch_operations=patch_operations,
    )

    print_item_patch_trace(
        label="valid_patch_operations",
        payload=valid_patch_operations,
    )

    if valid_patch_operations is None:
        print_item_patch_trace(
            label="patch_failure",
            payload={
                "reason": "invalid_patch_operations",
                "user_message": state.get("user_message"),
                "target_day_number": target_day_number,
            },
        )

        return create_item_patch_failure_result(
            existing_itinerary_days=existing_itinerary_days,
        )

    # ── 패치 적용 ────────────────────────────────────────────
    modified_day = apply_item_patch_operations(
        existing_day=existing_day,
        patch_operations=valid_patch_operations,
    )

    print_item_patch_trace(
        label="modified_day_items",
        payload=modified_day.get("items", []),
    )

    # 수정된 Day를 전체 일정에 병합
    merged_itinerary_days = merge_modified_day_into_itinerary(
        existing_itinerary_days=existing_itinerary_days,
        modified_day=modified_day,
    )

    return {
        "itinerary_days": merged_itinerary_days,
        "agent_response": patch_result.agent_response,
    }


# ══════════════════════════════════════════════════════════════
# 13. LLM 기반 Day 전체 교체
# ══════════════════════════════════════════════════════════════

def modify_itinerary_cards_with_llm(
    state: TravelAgentState,
) -> dict[str, object] | None:
    """기존 itinerary_days를 유지하면서 자연어 요청에 맞게 특정 Day만 수정합니다.

    카드 단위 patch가 부적합할 때(can_apply_as_item_patch=False) 호출되는
    2차 수정 전략입니다. 대상 Day의 비고정 item 전체를 새로 생성합니다.

    Args:
        state: 현재 LangGraph 상태.

    Returns:
        dict | None — 수정 성공 시 itinerary_days + agent_response.
                      실패 시 None.
    """

    if not os.getenv("OPENAI_API_KEY"):
        return None

    try:
        from langchain_openai import ChatOpenAI
        from pydantic import BaseModel, Field
    except ImportError:
        return None

    # ── Pydantic Structured Output 스키마 ────────────────────
    class ReplacementItineraryItemOutput(BaseModel):
        """비고정 item을 대체할 새 item."""

        time: str = Field(description="수정된 일정 시간. 예: 10:00, 13:30")
        title: str = Field(description="UI 카드에 표시할 짧은 일정 제목")
        description: str = Field(description="사용자 수정 요청을 반영한 짧은 설명")
        travel_time: str = Field(description="이전 일정에서 이 일정까지의 대략적인 이동 시간")

    class ModifiedDayOutput(BaseModel):
        """Day 전체 수정 결과."""

        title: str = Field(description="수정된 Day 제목. 예: Day 2")
        replacement_items: list[ReplacementItineraryItemOutput] = Field(
            description=(
                "고정되지 않은 기존 item을 대체할 새 일정 item 목록. "
                "is_fixed=True인 기존 item은 포함하지 않는다."
            )
        )
        agent_response: str = Field(
            description="사용자에게 보여줄 짧은 한국어 응답"
        )

    existing_itinerary_days = state.get("itinerary_days", [])
    target_day_number = resolve_target_day_number_for_modification(state)

    existing_day = find_itinerary_day_by_number(
        itinerary_days=existing_itinerary_days,
        day_number=target_day_number,
    )

    if existing_day is None:
        return {
            "agent_response": (
                f"Day {target_day_number} 일정을 찾지 못했습니다. "
                "수정할 Day를 다시 지정해 주세요."
            )
        }

    existing_items = existing_day.get("items", [])
    fixed_items = get_fixed_items_from_day(existing_day)

    # 수정 가능한(비고정) item 수 계산
    modifiable_item_count = len(
        [
            existing_item
            for existing_item in existing_items
            if not existing_item.get("is_fixed")
        ]
    )

    # 모든 item이 고정되어 있으면 수정할 것이 없음
    if modifiable_item_count <= 0:
        return {
            "itinerary_days": deepcopy(existing_itinerary_days),
            "agent_response": (
                f"Day {target_day_number}의 모든 카드가 고정되어 있어 "
                "수정할 수 있는 카드가 없습니다."
            ),
        }

    travel_condition_summary = build_travel_condition_summary(
        state.get("travel_conditions", [])
    )

    # ── 시스템 프롬프트 ──────────────────────────────────────
    # 핵심: "replacement_items 개수는 반드시 {modifiable_item_count}개"
    # → LLM이 고정 item은 건드리지 않고, 정확한 수만큼 대체 item을 생성
    system_prompt = f"""
너는 제주 여행 플래너 앱의 기존 일정 수정 노드다.

현재 앱은 제주 여행만 지원한다.
너는 기존 itinerary_days를 기반으로 사용자의 자연어 수정 요청을 반영해야 한다.

중요 규칙:
1. 전체 일정을 새로 만들지 말고 Day {target_day_number}만 수정한다.
2. Day {target_day_number} 외의 다른 Day는 수정하지 않는다.
3. is_fixed=True인 기존 item은 절대 삭제, 변경, 요약, 대체하지 않는다.
4. replacement_items에는 is_fixed=True인 기존 item을 포함하지 않는다.
5. replacement_items는 고정되지 않은 기존 item을 대체할 새 item만 포함한다.
6. replacement_items 개수는 반드시 {modifiable_item_count}개로 만든다.
7. 일정 내용은 사용자 자연어 요청과 현재 State만 근거로 만든다.
8. 코드 안에 저장된 장소 후보 목록이나 샘플 일정이 있다고 가정하지 마라.
9. 제주 외 지역 일정은 생성하지 않는다.
10. 주소, 위도, 경도, place_id는 만들지 않는다.
11. 하루 동선이 과도하게 흩어지지 않도록 같은 권역 중심으로 구성한다.
12. time, title, description, travel_time은 UI에 바로 표시 가능하게 작성한다.
13. 반환 형식은 structured output schema를 반드시 따른다.
"""

    user_prompt = f"""
현재 State 요약:
destination_name: {state.get("destination_name")}
trip_day_count: {state.get("trip_day_count")}
selected_day_number: {state.get("selected_day_number")}
target_day_number: {target_day_number}
travel_conditions: {travel_condition_summary}

전체 기존 itinerary_days:
{existing_itinerary_days}

수정 대상 기존 Day:
{existing_day}

수정 중 반드시 유지해야 하는 fixed_items:
{fixed_items}

사용자 자연어 수정 요청:
{state.get("user_message")}
"""

    chat_model = ChatOpenAI(
        model=os.getenv("TRAVEL_AGENT_MODEL", "gpt-4o-mini"),
        temperature=0,
    )

    structured_model = chat_model.with_structured_output(ModifiedDayOutput)

    try:
        modification_result = structured_model.invoke(
            [
                ("system", system_prompt),
                ("human", user_prompt),
            ]
        )
    except Exception:
        return None

    # 생성된 replacement 수가 기대와 다르면 실패
    if len(modification_result.replacement_items) != modifiable_item_count:
        return None

    # ── replacement_items를 내부 형식으로 변환 ────────────────
    replacement_items: list[ItineraryItem] = []

    for item_index, item_output in enumerate(
        modification_result.replacement_items,
        start=1,
    ):
        replacement_items.append(
            create_modified_itinerary_item(
                day_number=target_day_number,
                item_index=item_index,
                time=item_output.time,
                title=item_output.title,
                description=item_output.description,
                travel_time=item_output.travel_time,
            )
        )

    # ── 고정 item과 병합 ────────────────────────────────────
    modified_day = merge_replacement_items_with_fixed_items(
        existing_day=existing_day,
        replacement_items=replacement_items,
    )

    # Day 제목 업데이트
    modified_day["title"] = (
        modification_result.title
        or existing_day.get("title", f"Day {target_day_number}")
    )

    # ── 전체 일정에 병합 ────────────────────────────────────
    merged_itinerary_days = merge_modified_day_into_itinerary(
        existing_itinerary_days=existing_itinerary_days,
        modified_day=modified_day,
    )

    return {
        "itinerary_days": merged_itinerary_days,
        "agent_response": modification_result.agent_response,
    }


# ══════════════════════════════════════════════════════════════
# 14. LangGraph 노드 함수 (외부 공개)
# ══════════════════════════════════════════════════════════════
# 아래 함수들이 travel_graph.py에서 노드로 등록됩니다.

def generate_itinerary_cards(state: TravelAgentState) -> dict[str, object]:
    """분석된 State를 바탕으로 일정 카드 데이터를 생성하거나 수정합니다.

    의사결정 흐름:
        1. trip_day_count가 없으면 → 여행 일수를 먼저 물어봄
        2. 기존 일정이 있으면 →
           a. 카드 단위 patch 시도 (patch_itinerary_items_with_llm)
           b. patch 부적합 + 의도가 수정이면 → Day 전체 교체 (modify_itinerary_cards_with_llm)
           c. 일반 질문이면 → 빈 dict 반환 (일정 변경 없음)
        3. 기존 일정이 없으면 → 최초 생성 (generate_itinerary_cards_with_llm)

    Args:
        state: 현재 LangGraph 상태.

    Returns:
        dict — itinerary_days, agent_response 등을 포함하는 부분 상태 업데이트.
    """

    trip_day_count = state.get("trip_day_count")
    existing_itinerary_days = state.get("itinerary_days", [])

    # ── 여행 일수가 아직 없는 경우 ───────────────────────────
    if trip_day_count is None:
        return {
            "agent_response": (
                "여행 일수를 먼저 알려주세요. 예를 들어 "
                "'제주 4박 5일 여행 짜줘'처럼 입력하면 일정 카드를 만들 수 있습니다."
            )
        }

    # ── 기존 일정이 있는 경우 (수정 흐름) ────────────────────
    if has_existing_itinerary_items(existing_itinerary_days):
        user_intent = state.get("user_intent", "general_question")

        # 1차: 카드 단위 patch 시도
        patched_result = patch_itinerary_items_with_llm(state)

        if patched_result is not None:
            return patched_result

        # 일반 질문이면 일정 변경 없이 종료
        if user_intent == "general_question":
            return {}

        # 2차: Day 전체 교체 시도
        modified_result = modify_itinerary_cards_with_llm(state)

        if modified_result is None:
            return {
                "agent_response": (
                    "일정 수정에 실패했습니다. "
                    "예를 들어 '둘째 날은 애월 중심으로 바꿔줘'처럼 "
                    "수정할 Day와 원하는 방향을 함께 입력해 주세요."
                )
            }

        return modified_result

    # ── 기존 일정이 없는 경우 (최초 생성) ────────────────────
    generated_result = generate_itinerary_cards_with_llm(state)

    if generated_result is None:
        return {
            "agent_response": (
                "일정 카드 생성에 실패했습니다. "
                "여행 기간, 동행자, 이동 방식, 원하는 분위기를 조금 더 구체적으로 입력해 주세요."
            )
        }

    return generated_result


def analyze_user_request(state: TravelAgentState) -> dict[str, object]:
    """사용자 입력을 분석하는 LangGraph 노드입니다.

    LLM 해석을 먼저 시도하고, 실패하면 fallback으로 전환합니다.
    이 이중 전략 덕분에 API 키가 없는 환경에서도 앱이 최소한으로 동작합니다.

    Args:
        state: 현재 LangGraph 상태.

    Returns:
        dict — user_intent, travel_conditions, target_day_number 등.
    """

    llm_result = interpret_user_request_with_llm(state)

    if llm_result is not None:
        return llm_result

    return fallback_interpret_user_request(state)


def create_agent_response(state: TravelAgentState) -> dict[str, str]:
    """Agent 응답 문장을 만드는 LangGraph 노드입니다.

    이전 노드(generate_itinerary_cards 등)에서 이미 agent_response가
    설정되었으면 그대로 사용합니다.
    fallback일 때만 기본 응답을 생성합니다.

    Args:
        state: 현재 LangGraph 상태.

    Returns:
        dict — agent_response 필드만 포함하는 부분 상태 업데이트.
    """

    existing_agent_response = state.get("agent_response")

    # 이미 응답이 있으면 그대로 전달
    if existing_agent_response:
        return {
            "agent_response": existing_agent_response,
        }

    # 응답이 없으면 user_intent에 따라 기본 응답 생성
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


def create_guardrail_response(state: TravelAgentState) -> dict[str, str]:
    """입력 가드레일에 걸렸을 때 사용자에게 보여줄 응답을 만듭니다.

    guard_jeju_scope에서 설정한 guardrail_message를 그대로 전달합니다.
    메시지가 없으면 기본 문구를 사용합니다.

    Args:
        state: 현재 LangGraph 상태.

    Returns:
        dict — agent_response 필드만 포함하는 부분 상태 업데이트.
    """

    return {
        "agent_response": state.get(
            "guardrail_message",
            "현재 버전에서 지원하지 않는 여행지입니다.",
        )
    }
