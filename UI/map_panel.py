"""
UI/map_panel.py — 중앙 지도(동선 미리보기) 패널 UI

대시보드의 중앙 영역을 구성합니다.
실제 지도 API 연동 전 단계에서, 선택된 Day의 일정을
번호 순서(동선)로 카드 형태로 표시합니다.

컴포넌트 구조:
    ┌────────────────────────────────────────┐
    │  "동선 미리보기"     [지도 API 전] [Day N] │
    │  안내 메시지                             │
    │                                        │
    │  ┌─ 동선 카드 ──────────────────────┐  │
    │  │ ① 성산일출봉           10:00     │  │
    │  │   부모님과 함께...      차로 20분  │  │
    │  └──────────────────────────────────┘  │
    │  ┌─ 동선 카드 ──────────────────────┐  │
    │  │ ② 점심 식당           12:00     │  │
    │  │   ...                           │  │
    │  └──────────────────────────────────┘  │
    │                                        │
    │     [장소 검색] [경로 검증] [숙소 보기]    │
    └────────────────────────────────────────┘

향후 개선:
    - 실제 지도 API(Kakao Maps, Google Maps 등) 연동 시
      동선 카드 대신 지도 위에 마커·경로를 표시합니다.
    - 하단 버튼(장소 검색, 경로 검증, 숙소 보기)에 실제 기능을 연결합니다.
"""

import flet as ft

from UI.theme import (
    CARD_BACKGROUND_COLOR,
    MAP_BACKGROUND_COLOR,
    PRIMARY_TEXT_COLOR,
    SECONDARY_TEXT_COLOR,
    TIME_TEXT_COLOR,
    TRAVEL_TIME_TEXT_COLOR,
    create_card_border,
    create_panel_border,
    create_pill_button,
)


# ──────────────────────────────────────────────────────────────
# 선택된 Day 데이터 조회
# ──────────────────────────────────────────────────────────────
def find_selected_map_day(
    itinerary_days: list[dict],
    selected_day_number: int,
) -> dict | None:
    """선택된 Day에 해당하는 일정 데이터를 찾습니다.

    itinerary_panel.py의 find_selected_itinerary_day()와 동일한 로직이지만,
    패널 간 결합도를 낮추기 위해 별도로 정의합니다.

    NOTE (검수 의견):
        itinerary_panel.py에도 동일한 함수가 있습니다.
        공통 유틸리티 모듈로 추출하면 코드 중복을 제거할 수 있습니다.

    Args:
        itinerary_days:      전체 Day 목록.
        selected_day_number: 현재 선택된 Day 번호.

    Returns:
        dict | None — 해당 Day 딕셔너리. 없으면 None.
    """

    for itinerary_day in itinerary_days:
        if itinerary_day.get("day_number") == selected_day_number:
            return itinerary_day

    return None


# ──────────────────────────────────────────────────────────────
# 동선 항목(Route Stop) 카드 생성
# ──────────────────────────────────────────────────────────────
def create_route_stop_control(
    schedule_item: dict,
    item_index: int,
) -> ft.Container:
    """지도 패널에 표시할 동선 항목 하나를 만듭니다.

    일정 카드와 유사하지만 레이아웃이 다릅니다:
    - 왼쪽에 원형 번호 뱃지
    - 중앙에 제목 + 설명
    - 오른쪽에 시간 + 이동 시간

    Args:
        schedule_item: ItineraryItem 딕셔너리.
        item_index:    동선 순서 번호 (1부터 시작).

    Returns:
        ft.Container — 동선 항목 카드.
    """

    return ft.Container(
        padding=12,
        border_radius=14,
        bgcolor=CARD_BACKGROUND_COLOR,
        border=create_card_border(),
        content=ft.Row(
            controls=[
                # ── 왼쪽: 원형 번호 뱃지 ─────────────────────
                ft.Container(
                    width=28,
                    height=28,
                    border_radius=14,           # 28/2 = 원형
                    alignment=ft.Alignment.CENTER,
                    bgcolor=MAP_BACKGROUND_COLOR,
                    border=create_card_border(),
                    content=ft.Text(
                        str(item_index),
                        size=12,
                        weight=ft.FontWeight.BOLD,
                        color=PRIMARY_TEXT_COLOR,
                    ),
                ),
                # ── 중앙: 제목 + 설명 ────────────────────────
                ft.Column(
                    expand=True,  # 남은 가로 공간을 차지
                    spacing=4,
                    controls=[
                        ft.Text(
                            schedule_item.get("title", "장소 미정"),
                            size=15,
                            weight=ft.FontWeight.BOLD,
                            color=PRIMARY_TEXT_COLOR,
                        ),
                        ft.Text(
                            schedule_item.get("description", ""),
                            size=12,
                            color=SECONDARY_TEXT_COLOR,
                            max_lines=2,                          # 최대 2줄
                            overflow=ft.TextOverflow.ELLIPSIS,    # 넘치면 말줄임표
                        ),
                    ],
                ),
                # ── 오른쪽: 시간 + 이동 시간 ─────────────────
                ft.Column(
                    spacing=4,
                    horizontal_alignment=ft.CrossAxisAlignment.END,  # 오른쪽 정렬
                    controls=[
                        ft.Text(
                            schedule_item.get("time", "시간 미정"),
                            size=12,
                            weight=ft.FontWeight.BOLD,
                            color=TIME_TEXT_COLOR,
                        ),
                        ft.Text(
                            schedule_item.get("travel_time", "이동 미정"),
                            size=11,
                            color=TRAVEL_TIME_TEXT_COLOR,
                        ),
                    ],
                ),
            ],
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )


# ──────────────────────────────────────────────────────────────
# 동선 없음 안내
# ──────────────────────────────────────────────────────────────
def create_empty_map_notice() -> ft.Container:
    """지도 패널에 표시할 일정 없음 안내를 만듭니다.

    Returns:
        ft.Container — 중앙 정렬된 안내 메시지.
    """

    return ft.Container(
        expand=True,
        alignment=ft.Alignment.CENTER,  # 상하좌우 중앙 정렬
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
            controls=[
                ft.Text(
                    "표시할 동선이 없습니다.",
                    size=16,
                    weight=ft.FontWeight.BOLD,
                    color=PRIMARY_TEXT_COLOR,
                ),
                ft.Text(
                    "오른쪽 여행 도우미에게 제주 여행 일정을 먼저 생성해 주세요.",
                    size=13,
                    color=SECONDARY_TEXT_COLOR,
                    text_align=ft.TextAlign.CENTER,
                ),
            ],
        ),
    )


# ──────────────────────────────────────────────────────────────
# 동선 카드 목록 빌드
# ──────────────────────────────────────────────────────────────
def build_route_stop_controls(
    itinerary_days: list[dict],
    selected_day_number: int,
) -> list[ft.Control]:
    """선택된 Day의 일정 item을 지도 패널용 동선 목록으로 변환합니다.

    Args:
        itinerary_days:      전체 일정 데이터.
        selected_day_number: 현재 선택된 Day 번호.

    Returns:
        list[ft.Control] — 동선 카드 컨트롤 목록.
    """

    selected_day = find_selected_map_day(
        itinerary_days=itinerary_days,
        selected_day_number=selected_day_number,
    )

    # Day가 없거나 items가 비어 있으면 안내 카드 반환
    if selected_day is None:
        return [create_empty_map_notice()]

    schedule_items = selected_day.get("items", [])

    if not schedule_items:
        return [create_empty_map_notice()]

    # enumerate(start=1)로 동선 번호를 1부터 매기기
    return [
        create_route_stop_control(
            schedule_item=schedule_item,
            item_index=item_index,
        )
        for item_index, schedule_item in enumerate(schedule_items, start=1)
    ]


# ──────────────────────────────────────────────────────────────
# 지도 패널 전체 생성
# ──────────────────────────────────────────────────────────────
def create_map_panel(
    selected_day_number: int,
    itinerary_days: list[dict],
) -> ft.Container:
    """중앙 지도 영역을 만듭니다.

    실제 지도 API 연결 전 단계에서는 선택된 Day의 일정 카드 목록을
    동선 순서로 보여줍니다.

    Args:
        selected_day_number: 현재 선택된 Day 번호.
        itinerary_days:      전체 일정 데이터.

    Returns:
        ft.Container — 지도 패널 전체 컨테이너.
    """

    total_day_count = len(itinerary_days)

    # 일정 존재 여부에 따라 상단 텍스트 변경
    if total_day_count > 0:
        day_label = f"Day {selected_day_number}"
        guide_message = "선택한 Day의 일정 순서를 기준으로 동선을 표시합니다."
    else:
        day_label = "일정 대기"
        guide_message = "먼저 오른쪽에 원하는 여행 조건을 입력하세요."

    return ft.Container(
        expand=True,
        padding=24,
        border_radius=16,
        bgcolor=MAP_BACKGROUND_COLOR,
        border=create_panel_border(),
        content=ft.Column(
            controls=[
                # ── 상단 헤더 행 ──────────────────────────────
                ft.Row(
                    controls=[
                        ft.Text(
                            "동선 미리보기",
                            size=22,
                            weight=ft.FontWeight.BOLD,
                            color=PRIMARY_TEXT_COLOR,
                        ),
                        ft.Container(expand=True),     # 좌우 끝 정렬용 스페이서
                        create_pill_button(
                            label="지도 API 전",        # 향후 지도 API 연동 상태 표시
                            width=108,
                            height=34,
                        ),
                        create_pill_button(
                            label=day_label,
                            is_selected=True,           # 항상 활성 상태로 표시
                            width=104,
                            height=34,
                        ),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                # ── 안내 메시지 ───────────────────────────────
                ft.Text(
                    guide_message,
                    size=13,
                    color=SECONDARY_TEXT_COLOR,
                ),
                # ── 동선 카드 목록 (스크롤) ───────────────────
                ft.ListView(
                    expand=True,
                    spacing=10,
                    padding=0,
                    controls=build_route_stop_controls(
                        itinerary_days=itinerary_days,
                        selected_day_number=selected_day_number,
                    ),
                ),
                # ── 하단 기능 버튼 행 ─────────────────────────
                # 현재는 동작하지 않는 플레이스홀더 버튼입니다.
                # 향후 지도 API 연동 시 실제 기능을 연결합니다.
                ft.Row(
                    controls=[
                        create_pill_button(
                            label="장소 검색",
                            width=108,
                            height=34,
                        ),
                        create_pill_button(
                            label="경로 검증",
                            width=108,
                            height=34,
                        ),
                        create_pill_button(
                            label="숙소 보기",
                            width=108,
                            height=34,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=10,
                ),
            ],
            spacing=12,
        ),
    )
