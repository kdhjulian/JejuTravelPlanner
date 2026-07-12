import flet as ft

from UI.theme import (
    MAP_BACKGROUND_COLOR,
    PRIMARY_TEXT_COLOR,
    SECONDARY_TEXT_COLOR,
    create_panel_border,
    create_pill_button,
)


def create_map_panel(
    selected_day_number: int,
    total_day_count: int,
) -> ft.Container:
    """중앙 지도 영역을 만듭니다."""

    if total_day_count > 0:
        day_label = f"Day {selected_day_number}"
        guide_message = "선택한 Day의 동선을 이 영역에서 확인할 수 있습니다."
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
                ft.Row(
                    controls=[
                        ft.Text(
                            "지도 영역",
                            size=22,
                            weight=ft.FontWeight.BOLD,
                            color=PRIMARY_TEXT_COLOR,
                        ),
                        ft.Container(expand=True),
                        create_pill_button(
                            label="전체 경로",
                            width=108,
                            height=34,
                        ),
                        create_pill_button(
                            label=day_label,
                            is_selected=True,
                            width=104,
                            height=34,
                        ),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Container(expand=True),
                ft.Text(
                    "Google Maps / Kakao Map / Naver Map 연결 전 플레이스홀더",
                    size=16,
                    color=SECONDARY_TEXT_COLOR,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    guide_message,
                    size=13,
                    color=SECONDARY_TEXT_COLOR,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(expand=True),
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
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )