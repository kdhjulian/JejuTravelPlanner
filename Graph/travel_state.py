"""
Graph/travel_state.py — LangGraph 상태(State) 타입 정의

LangGraph에서 노드 간에 주고받는 모든 데이터의 스키마를 정의합니다.
TypedDict를 사용해 런타임 오버헤드 없이 타입 힌트만 제공하며,
mypy·pyright 등 정적 분석 도구가 타입 불일치를 검출할 수 있게 합니다.

구조 개요:
    TravelAgentState           ← LangGraph 전체 상태 (최상위)
    ├── TravelCondition        ← 사용자 입력에서 추출한 개별 여행 조건
    ├── ItineraryDay           ← Day 단위 일정
    │   └── ItineraryItem      ← Day 안의 개별 장소/활동 카드
    └── TravelUserIntent       ← 사용자 의도 분류 리터럴 타입
"""

from typing import Literal, NotRequired, TypedDict


# ──────────────────────────────────────────────────────────────
# 사용자 의도(Intent) 리터럴 타입
# ──────────────────────────────────────────────────────────────
# LLM이 사용자 메시지를 분석한 뒤 결정하는 "의도" 분류입니다.
# Literal을 사용해 허용되는 값을 컴파일 타임에 제한합니다.
#
# 각 값의 의미:
#   create_initial_trip  — 여행 일정을 처음 생성
#   change_itinerary     — 기존 일정을 수정
#   recommend_place      — 특정 장소 추천 요청
#   check_route          — 동선/경로 확인 요청
#   update_condition     — 여행 조건만 변경 (일정 변경 없이)
#   general_question     — 위에 해당하지 않는 일반 질문
TravelUserIntent = Literal[
    "create_initial_trip",
    "change_itinerary",
    "recommend_place",
    "check_route",
    "update_condition",
    "general_question",
]


# ──────────────────────────────────────────────────────────────
# 여행 조건(Travel Condition)
# ──────────────────────────────────────────────────────────────
# 사용자의 자연어 입력에서 LLM이 추출한 개별 조건 하나를 나타냅니다.
# UI에서는 이 객체의 `label` 필드를 칩(Chip) 형태로 표시합니다.
class TravelCondition(TypedDict):
    """사용자 자연어에서 추출한 여행 조건입니다.

    category:
        companion, transport, lodging, preference 같은 분류입니다.
        단, 고정 enum이 아니라 LLM이 필요하면 새로운 category를 만들 수 있습니다.
        → 열린 분류 체계(open taxonomy)를 채택한 설계입니다.

    label:
        UI 칩에 보여줄 짧은 문자열입니다.
        예: "부모님 동반", "렌터카", "애월 숙소", "조용한 여행", "반려견 동반"

    raw_text:
        사용자가 실제로 입력한 원문 근거입니다.
        디버깅 및 LLM 재입력 시 맥락 유지에 사용됩니다.

    confidence:
        LLM이 판단한 신뢰도(0.0~1.0)입니다.
        현재 UI에서는 표시하지 않지만, 향후 낮은 신뢰도 조건을
        사용자에게 확인 요청하는 데 활용할 수 있습니다.
    """

    category: str       # 조건 분류 (예: "companion", "transport", "lodging")
    label: str          # UI 칩에 표시할 짧은 한국어 문자열
    raw_text: str       # 사용자 원문에서 발췌한 근거 텍스트
    confidence: float   # LLM 판단 신뢰도 (0.0 ~ 1.0)


# ──────────────────────────────────────────────────────────────
# 일정 아이템(Itinerary Item)
# ──────────────────────────────────────────────────────────────
# 하루 일정 안에 들어가는 개별 장소/활동 카드 하나입니다.
# UI의 일정 카드(itinerary_panel.py)와 1:1로 대응됩니다.
class ItineraryItem(TypedDict):
    """하루 일정 안에 들어가는 장소/활동 카드입니다."""

    item_id: str
    time: str

    title: str

    description: str
    travel_time: str
    is_fixed: bool
    source: str

    # API 연동 전 AI 기반 장소 추정 필드입니다.
    is_place_specific: NotRequired[bool]
    place_name: NotRequired[str]
    place_area: NotRequired[str]
    place_category: NotRequired[str]
    place_selection_reason: NotRequired[str]
    search_query: NotRequired[str]
    place_verification_status: NotRequired[str]


# ──────────────────────────────────────────────────────────────
# Day 단위 일정(Itinerary Day)
# ──────────────────────────────────────────────────────────────
# Day 1, Day 2, ... 각각에 대응하는 단위입니다.
# items 필드에 ItineraryItem 목록을 담습니다.
class ItineraryDay(TypedDict):
    """Day 단위 일정입니다."""

    day_number: int             # Day 번호 (1부터 시작)
    title: str                  # Day 제목 (예: "Day 1", "서귀포 해안 탐방")
    items: list[ItineraryItem]  # 해당 Day의 일정 카드 목록


# ──────────────────────────────────────────────────────────────
# LangGraph 전체 상태(Travel Agent State)
# ──────────────────────────────────────────────────────────────
# LangGraph의 StateGraph에 전달되는 최상위 상태 딕셔너리입니다.
# 모든 노드(guard_jeju_scope, analyze_user_request, generate_itinerary_cards 등)가
# 이 상태를 읽고 쓰며, 노드 반환값으로 부분 업데이트(partial update)합니다.
#
# NotRequired 필드는 노드 실행 단계에 따라 있을 수도, 없을 수도 있습니다.
# 예: guardrail_blocked는 guard_jeju_scope 노드 실행 후에만 존재합니다.
class TravelAgentState(TypedDict):
    """여행 Agent가 LangGraph 안에서 주고받는 상태입니다."""

    # ── 필수 필드 (항상 존재) ─────────────────────────────────
    user_message: str           # 사용자가 입력한 원본 메시지
    selected_day_number: int    # UI에서 현재 선택된 Day 번호

    # ── 선택 필드 (노드 실행 단계에 따라 추가) ────────────────
    destination_name: NotRequired[str]                  # 여행지 이름 (현재는 항상 "제주")
    user_intent: NotRequired[TravelUserIntent]          # LLM이 분석한 사용자 의도
    target_day_number: NotRequired[int]                 # 수정 대상 Day 번호

    trip_day_count: NotRequired[int]                    # 총 여행 일수 (예: 5)
    travel_conditions: NotRequired[list[TravelCondition]]  # 추출된 여행 조건 목록
    itinerary_days: NotRequired[list[ItineraryDay]]     # 전체 Day별 일정 데이터

    agent_response: NotRequired[str]                    # 에이전트가 사용자에게 보여줄 응답 메시지

    # ── 입력 가드레일(Input Guardrails) 관련 필드 ─────────────
    guardrail_blocked: NotRequired[bool]                # 가드레일에 의해 차단되었는지 여부
    guardrail_message: NotRequired[str]                 # 차단 시 사용자에게 보여줄 메시지
    guardrail_reason: NotRequired[str]                  # 차단 사유 (한국어 설명)
    detected_destination: NotRequired[str | None]       # 가드레일이 감지한 여행지 (없으면 None)
