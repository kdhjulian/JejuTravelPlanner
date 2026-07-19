"""
UI/itinerary_panel.py — 왼쪽 여행 일정 패널 UI

대시보드의 왼쪽 영역을 구성합니다.
상단에 Day 버튼 목록을 표시하고, 하단에 선택된 Day의 일정 카드를 나열합니다.

컴포넌트 구조:
    ┌──────────────────────────────────┐
    │  "여행 일정" (제목)               │
    │  [Day 1] [Day 2] [Day 3] ...    │  ← Day 선택 버튼 (wrap 가능)
    │                                  │
    │  ┌──── 일정 카드 ─────────────┐  │
    │  │ 10:00          차로 20분   │  │
    │  │ 성산일출봉                  │  │
    │  │ 부모님과 함께 여유있게...    │  │
    │  │ [위] [아래] [삭제] [고정]  │  │
    │  └────────────────────────────┘  │
    │                                  │
    │  ┌──── 일정 카드 ─────────────┐  │
    │  │ ...                        │  │
    │  └────────────────────────────┘  │
    └──────────────────────────────────┘
"""

import flet as ft

from UI.theme import (
    CARD_BACKGROUND_COLOR,
    PANEL_BACKGROUND_COLOR,
    PRIMARY_TEXT_COLOR,
    SECONDARY_TEXT_COLOR,
    TIME_TEXT_COLOR,
    TRAVEL_TIME_TEXT_COLOR,
    create_card_border,
    create_panel_border,
    create_pill_button,
)

# ──────────────────────────────────────────────────────────────
# Day 버튼 생성
# ──────────────────────────────────────────────────────────────
def create_day_button(
    day_number: int,
    selected_day_number: int,
    on_day_click,
) -> ft.Container:
    """Day 버튼을 만듭니다.

    현재 선택된 Day와 일치하면 활성(하이라이트) 상태로 표시됩니다.
    클릭 시 on_day_click 핸들러가 호출되며, event.control.data에
    day_number가 전달됩니다.

    Args:
        day_number:          이 버튼이 나타내는 Day 번호.
        selected_day_number: 현재 UI에서 선택된 Day 번호.
        on_day_click:        클릭 이벤트 핸들러.

    Returns:
        ft.Container — pill 형태의 Day 버튼.
    """

    return create_pill_button(
        label=f"Day {day_number}",
        is_selected=day_number == selected_day_number,  # 선택 상태 비교
        width=92,
        height=34,
        on_click=on_day_click,
        data=day_number,  # 핸들러에서 int(event.control.data)로 접근
    )


# ──────────────────────────────────────────────────────────────
# 빈 일정 안내 카드
# ──────────────────────────────────────────────────────────────
def create_empty_itinerary_notice(day_number: int) -> ft.Container:
    """아직 일정이 없는 Day에 표시할 안내 카드입니다.

    Day는 존재하지만 items 목록이 비어 있을 때 사용됩니다.

    Args:
        day_number: 해당 Day 번호.

    Returns:
        ft.Container — 안내 메시지가 담긴 카드.
    """

    return ft.Container(
        padding=14,
        border_radius=14,
        bgcolor=CARD_BACKGROUND_COLOR,
        border=create_card_border(),
        content=ft.Column(
            controls=[
                ft.Text(
                    f"Day {day_number} 일정이 아직 비어 있습니다.",
                    size=15,
                    weight=ft.FontWeight.BOLD,
                    color=PRIMARY_TEXT_COLOR,
                ),
                ft.Text(
                    "오른쪽 여행 도우미에게 원하는 장소, 분위기, 동선을 입력하면 "
                    "이곳에 일정 카드가 추가될 예정입니다.",
                    size=13,
                    color=SECONDARY_TEXT_COLOR,
                ),
            ],
            spacing=6,
        ),
    )

def build_place_meta_text(schedule_item: dict) -> str:
    """일정 카드에 표시할 장소 메타 정보를 만듭니다."""

    place_category = str(schedule_item.get("place_category", "")).strip()
    place_area = str(schedule_item.get("place_area", "")).strip()
    verification_status = str(
        schedule_item.get("place_verification_status", "")
    ).strip()

    meta_parts = []

    if place_category:
        meta_parts.append(place_category)

    if place_area:
        meta_parts.append(place_area)

    if verification_status == "ai_unverified":
        meta_parts.append("AI 장소 추정")
    elif verification_status == "api_verified":
        meta_parts.append("장소 검증 완료")
    elif verification_status:
        meta_parts.append(verification_status)

    return " · ".join(meta_parts)


def build_search_query_text(schedule_item: dict) -> str:
    """API 연동 전 단계에서 장소 검색어를 카드에 표시합니다."""

    search_query = str(schedule_item.get("search_query", "")).strip()

    if not search_query:
        return ""

    return f"검색어: {search_query}"

# ──────────────────────────────────────────────────────────────
# 일정 카드 생성
# ──────────────────────────────────────────────────────────────
def create_itinerary_card(
    schedule_item: dict,
    day_number: int,
    on_move_item_up,
    on_move_item_down,
    on_delete_item,
    on_toggle_fixed_item,
) -> ft.Container:
    """일정 카드 하나를 만듭니다."""

    button_data = {
        "day_number": day_number,
        "item_id": schedule_item.get("item_id"),
    }

    fixed_button_label = (
        "고정됨"
        if schedule_item.get("is_fixed")
        else "고정"
    )

    place_meta_text = build_place_meta_text(schedule_item)
    search_query_text = build_search_query_text(schedule_item)

    return ft.Container(
        padding=12,
        border_radius=14,
        bgcolor=CARD_BACKGROUND_COLOR,
        border=create_card_border(),
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text(
                            schedule_item.get("time", "시간 미정"),
                            size=14,
                            weight=ft.FontWeight.BOLD,
                            color=TIME_TEXT_COLOR,
                        ),
                        ft.Container(expand=True),
                        ft.Text(
                            schedule_item.get("travel_time", "이동 미정"),
                            size=12,
                            weight=ft.FontWeight.BOLD,
                            color=TRAVEL_TIME_TEXT_COLOR,
                        ),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Text(
                    schedule_item.get("title", "장소 미정"),
                    size=17,
                    weight=ft.FontWeight.BOLD,
                    color=PRIMARY_TEXT_COLOR,
                ),
                ft.Text(
                    place_meta_text,
                    size=11,
                    color=SECONDARY_TEXT_COLOR,
                    visible=bool(place_meta_text),
                ),
                ft.Text(
                    search_query_text,
                    size=10,
                    color=SECONDARY_TEXT_COLOR,
                    visible=bool(search_query_text),
                ),
                ft.Text(
                    schedule_item.get("description", ""),
                    size=13,
                    color=SECONDARY_TEXT_COLOR,
                ),
                ft.Row(
                    controls=[
                        create_pill_button(
                            label="위",
                            width=50,
                            height=28,
                            tooltip="위로 이동",
                            data=button_data,
                            on_click=on_move_item_up,
                        ),
                        create_pill_button(
                            label="아래",
                            width=56,
                            height=28,
                            tooltip="아래로 이동",
                            data=button_data,
                            on_click=on_move_item_down,
                        ),
                        create_pill_button(
                            label="삭제",
                            width=56,
                            height=28,
                            tooltip="삭제",
                            data=button_data,
                            on_click=on_delete_item,
                        ),
                        create_pill_button(
                            label=fixed_button_label,
                            width=68,
                            height=28,
                            tooltip="고정",
                            data=button_data,
                            on_click=on_toggle_fixed_item,
                        ),
                    ],
                    spacing=6,
                ),
            ],
            spacing=6,
        ),
    )


# ──────────────────────────────────────────────────────────────
# 선택된 Day 데이터 조회
# ──────────────────────────────────────────────────────────────
def find_selected_itinerary_day(
    itinerary_days: list[dict],
    selected_day_number: int,
) -> dict | None:
    """선택된 Day 데이터를 찾습니다.

    Args:
        itinerary_days:      전체 Day 목록.
        selected_day_number: 현재 선택된 Day 번호.

    Returns:
        dict | None — 해당 Day 딕셔너리. 없으면 None.
    """

    for itinerary_day in itinerary_days:
        if itinerary_day["day_number"] == selected_day_number:
            return itinerary_day

    return None


# ──────────────────────────────────────────────────────────────
# 일정 카드 목록 빌드
# ──────────────────────────────────────────────────────────────
def build_itinerary_cards(
    itinerary_days: list[dict],
    selected_day_number: int,
    on_move_item_up,
    on_move_item_down,
    on_delete_item,
    on_toggle_fixed_item,
) -> list[ft.Control]:
    """선택된 Day 번호에 맞는 일정 카드 목록을 만듭니다.

    세 가지 분기:
        1. itinerary_days가 비어 있으면 → "아직 여행 조건이 입력되지 않았습니다" 안내
        2. 선택된 Day가 없거나 items가 비어 있으면 → "Day N 일정이 비어 있습니다" 안내
        3. items가 있으면 → 각 item을 일정 카드로 변환

    Args:
        itinerary_days:      전체 일정 데이터.
        selected_day_number: 현재 선택된 Day 번호.
        on_move_item_up:     위로 이동 핸들러.
        on_move_item_down:   아래로 이동 핸들러.
        on_delete_item:      삭제 핸들러.
        on_toggle_fixed_item: 고정 토글 핸들러.

    Returns:
        list[ft.Control] — ListView에 넣을 컨트롤 목록.
    """

    # ── 분기 1: 전체 일정이 아직 없는 경우 ──────────────────
    if not itinerary_days:
        return [
            create_no_trip_notice(),
        ]

    # ── 분기 2: 선택된 Day가 없거나 items가 비어 있는 경우 ──
    selected_itinerary_day = find_selected_itinerary_day(
        itinerary_days=itinerary_days,
        selected_day_number=selected_day_number,
    )

    if selected_itinerary_day is None:
        return [
            create_empty_itinerary_notice(selected_day_number),
        ]

    schedule_items = selected_itinerary_day.get("items", [])

    if not schedule_items:
        return [
            create_empty_itinerary_notice(selected_day_number),
        ]

    # ── 분기 3: 정상 — 각 item을 카드로 변환 ─────────────────
    return [
        create_itinerary_card(
            schedule_item=schedule_item,
            day_number=selected_day_number,
            on_move_item_up=on_move_item_up,
            on_move_item_down=on_move_item_down,
            on_delete_item=on_delete_item,
            on_toggle_fixed_item=on_toggle_fixed_item,
        )
        for schedule_item in schedule_items
    ]


# ──────────────────────────────────────────────────────────────
# 일정 패널 전체 생성
# ──────────────────────────────────────────────────────────────
def create_itinerary_panel(
    itinerary_days: list[dict],
    selected_day_number: int,
    on_day_click,
    on_move_item_up,
    on_move_item_down,
    on_delete_item,
    on_toggle_fixed_item,
) -> ft.Container:
    """왼쪽 일정 패널을 만듭니다.

    Day 버튼 목록과 일정 카드 ListView를 수직으로 배치합니다.

    Args:
        itinerary_days:      전체 일정 데이터.
        selected_day_number: 현재 선택된 Day 번호.
        on_day_click:        Day 버튼 클릭 핸들러.
        on_move_item_up:     위로 이동 핸들러.
        on_move_item_down:   아래로 이동 핸들러.
        on_delete_item:      삭제 핸들러.
        on_toggle_fixed_item: 고정 토글 핸들러.

    Returns:
        ft.Container — 일정 패널 전체 컨테이너.
    """

    # ── 일정 카드 목록 (스크롤 가능) ─────────────────────────
    itinerary_list = ft.ListView(
        expand=True,     # 남은 세로 공간을 모두 차지
        spacing=10,      # 카드 간 간격
        padding=0,
        controls=build_itinerary_cards(
            itinerary_days=itinerary_days,
            selected_day_number=selected_day_number,
            on_move_item_up=on_move_item_up,
            on_move_item_down=on_move_item_down,
            on_delete_item=on_delete_item,
            on_toggle_fixed_item=on_toggle_fixed_item,
        ),
    )

    # ── Day 버튼 목록 또는 안내 메시지 ───────────────────────
    if itinerary_days:
        # 일정이 있으면 각 Day에 대한 버튼 생성
        day_buttons = [
            create_day_button(
                day_number=itinerary_day["day_number"],
                selected_day_number=selected_day_number,
                on_day_click=on_day_click,
            )
            for itinerary_day in itinerary_days
        ]
    else:
        # 일정이 없으면 안내 텍스트 표시
        day_buttons = [
            ft.Text(
                "먼저 오른쪽에 원하는 여행 일정을 입력하세요.",
                size=13,
                color=SECONDARY_TEXT_COLOR,
            )
        ]

    # ── 패널 레이아웃 조립 ───────────────────────────────────
    return ft.Container(
        expand=True,
        padding=16,
        bgcolor=PANEL_BACKGROUND_COLOR,
        border_radius=16,
        border=create_panel_border(),
        content=ft.Column(
            controls=[
                # 패널 제목
                ft.Text(
                    "여행 일정",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    color=PRIMARY_TEXT_COLOR,
                ),
                # Day 버튼 행 (wrap=True로 줄바꿈 가능)
                ft.Row(
                    controls=day_buttons,
                    spacing=8,
                    wrap=True,
                ),
                # 일정 카드 목록 (스크롤)
                itinerary_list,
            ],
            spacing=12,
        ),
    )


# ──────────────────────────────────────────────────────────────
# 여행 미생성 안내 카드
# ──────────────────────────────────────────────────────────────
def create_no_trip_notice() -> ft.Container:
    """아직 여행 조건이 입력되지 않았을 때 표시할 안내 카드입니다.

    itinerary_days 자체가 빈 리스트일 때 사용됩니다.
    (create_empty_itinerary_notice와 구분: 후자는 Day는 있지만 items가 빈 경우)

    Returns:
        ft.Container — 안내 메시지가 담긴 카드.
    """

    return ft.Container(
        padding=14,
        border_radius=14,
        bgcolor=CARD_BACKGROUND_COLOR,
        border=create_card_border(),
        content=ft.Column(
            controls=[
                ft.Text(
                    "아직 생성된 여행 일정이 없습니다.",
                    size=15,
                    weight=ft.FontWeight.BOLD,
                    color=PRIMARY_TEXT_COLOR,
                ),
                ft.Text(
                    "오른쪽 여행 도우미에게 제주 여행 기간, 동행자, 이동 방식, "
                    "숙소 조건, 원하는 분위기를 입력해 주세요.",
                    size=13,
                    color=SECONDARY_TEXT_COLOR,
                ),
            ],
            spacing=6,
        ),
    )
