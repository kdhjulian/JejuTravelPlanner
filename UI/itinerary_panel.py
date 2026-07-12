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


def create_day_button(
    day_number: int,
    selected_day_number: int,
    on_day_click,
) -> ft.Container:
    """Day 버튼을 만듭니다."""

    return create_pill_button(
        label=f"Day {day_number}",
        is_selected=day_number == selected_day_number,
        width=92,
        height=34,
        on_click=on_day_click,
        data=day_number,
    )


def create_empty_itinerary_notice(day_number: int) -> ft.Container:
    """아직 일정이 없는 Day에 표시할 안내 카드입니다."""

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


def create_itinerary_card(schedule_item: dict[str, str]) -> ft.Container:
    """일정 카드 하나를 만듭니다."""

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
                            on_click=lambda event: None,
                        ),
                        create_pill_button(
                            label="아래",
                            width=56,
                            height=28,
                            tooltip="아래로 이동",
                            on_click=lambda event: None,
                        ),
                        create_pill_button(
                            label="삭제",
                            width=56,
                            height=28,
                            tooltip="삭제",
                            on_click=lambda event: None,
                        ),
                        create_pill_button(
                            label="고정",
                            width=56,
                            height=28,
                            tooltip="고정",
                            on_click=lambda event: None,
                        ),
                    ],
                    spacing=6,
                ),
            ],
            spacing=6,
        ),
    )


def find_selected_itinerary_day(
    itinerary_days: list[dict],
    selected_day_number: int,
) -> dict | None:
    """선택된 Day 데이터를 찾습니다."""

    for itinerary_day in itinerary_days:
        if itinerary_day["day_number"] == selected_day_number:
            return itinerary_day

    return None


def build_itinerary_cards(
    itinerary_days: list[dict],
    selected_day_number: int,
) -> list[ft.Control]:
    """선택된 Day 번호에 맞는 일정 카드 목록을 만듭니다."""

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

    return [
        create_itinerary_card(schedule_item)
        for schedule_item in schedule_items
    ]


def create_itinerary_panel(
    itinerary_days: list[dict],
    selected_day_number: int,
    on_day_click,
) -> ft.Container:
    """왼쪽 일정 패널을 만듭니다."""

    itinerary_list = ft.ListView(
        expand=True,
        spacing=10,
        padding=0,
        controls=build_itinerary_cards(
            itinerary_days=itinerary_days,
            selected_day_number=selected_day_number,
        ),
    )

    if itinerary_days:
        day_buttons = [
            create_day_button(
                day_number=itinerary_day["day_number"],
                selected_day_number=selected_day_number,
                on_day_click=on_day_click,
            )
            for itinerary_day in itinerary_days
        ]
    else:
        day_buttons = [
            ft.Text(
                "먼저 오른쪽에 원하는 여행 일정을 입력하세요.",
                size=13,
                color=SECONDARY_TEXT_COLOR,
            )
        ]

    return ft.Container(
        expand=True,
        padding=16,
        bgcolor=PANEL_BACKGROUND_COLOR,
        border_radius=16,
        border=create_panel_border(),
        content=ft.Column(
            controls=[
                ft.Text(
                    "여행 일정",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    color=PRIMARY_TEXT_COLOR,
                ),
                ft.Row(
                    controls=day_buttons,
                    spacing=8,
                    wrap=True,
                ),
                itinerary_list,
            ],
            spacing=12,
        ),
    )