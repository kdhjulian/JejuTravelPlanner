import flet as ft

from UI.theme import (
    ACCENT_STRONG_COLOR,
    AGENT_MESSAGE_BACKGROUND_COLOR,
    AGENT_MESSAGE_TEXT_COLOR,
    PANEL_BACKGROUND_COLOR,
    PRIMARY_TEXT_COLOR,
    SECONDARY_TEXT_COLOR,
    USER_MESSAGE_BACKGROUND_COLOR,
    USER_MESSAGE_TEXT_COLOR,
    create_condition_chip,
    create_divider,
    create_panel_border,
    create_primary_button,
)

def create_chat_message(role: str, message: str) -> ft.Container:
    """채팅 메시지 말풍선을 만듭니다."""

    is_user_message = role == "user"

    role_label = "나" if is_user_message else "여행 도우미"

    background_color = (
        USER_MESSAGE_BACKGROUND_COLOR
        if is_user_message
        else AGENT_MESSAGE_BACKGROUND_COLOR
    )

    message_color = (
        USER_MESSAGE_TEXT_COLOR
        if is_user_message
        else AGENT_MESSAGE_TEXT_COLOR
    )

    role_color = USER_MESSAGE_TEXT_COLOR if is_user_message else ACCENT_STRONG_COLOR

    return ft.Container(
        padding=12,
        border_radius=12,
        bgcolor=background_color,
        content=ft.Column(
            controls=[
                ft.Text(
                    role_label,
                    size=12,
                    weight=ft.FontWeight.BOLD,
                    color=role_color,
                ),
                ft.Text(
                    message,
                    size=13,
                    color=message_color,
                ),
            ],
            spacing=4,
        ),
    )


def create_understood_condition_chip(label: str) -> ft.Container:
    """Agent가 이해한 여행 조건을 작은 칩 형태로 표시합니다."""

    return ft.Container(
        padding=ft.Padding.symmetric(horizontal=10, vertical=6),
        border_radius=999,
        bgcolor="#162A41",
        content=ft.Text(
            label,
            size=12,
            color="#90A7B0",
        ),
    )

def get_condition_label(travel_condition) -> str:
    """조건 객체 또는 문자열에서 UI 표시용 label을 꺼냅니다."""

    if isinstance(travel_condition, dict):
        return travel_condition.get("label", "조건")

    return str(travel_condition)


def create_agent_panel(
    chat_message_list: ft.ListView,
    user_message_input: ft.TextField,
    on_send_message,
    travel_condition_chips: list[str],
) -> ft.Container:
    """오른쪽 여행 도우미 패널 전체를 만듭니다."""

    if travel_condition_chips:
        understood_conditions_controls = [
            create_condition_chip(get_condition_label(travel_condition))
            for travel_condition in travel_condition_chips
        ]
    else:
        understood_conditions_controls = [
            create_condition_chip("조건 대기 중"),
        ]

    understood_conditions = ft.Row(
        controls=understood_conditions_controls,
        wrap=True,
        spacing=8,
        run_spacing=8,
    )

    send_button = create_primary_button(
        label="전송",
        width=76,
        height=34,
        on_click=on_send_message,
    )

    return ft.Container(
        expand=True,
        padding=16,
        bgcolor=PANEL_BACKGROUND_COLOR,
        border_radius=16,
        border=create_panel_border(),
        content=ft.Column(
            controls=[
                ft.Text(
                    "제주 여행 도우미",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    color=PRIMARY_TEXT_COLOR,
                ),
                ft.Text(
                    "먼저 원하는 여행 조건을 자연어로 입력하세요.",
                    size=12,
                    color=SECONDARY_TEXT_COLOR,
                ),
                ft.Text(
                    "현재 여행 조건",
                    size=13,
                    weight=ft.FontWeight.BOLD,
                    color=PRIMARY_TEXT_COLOR,
                ),
                understood_conditions,
                create_divider(),
                chat_message_list,
                ft.Row(
                    controls=[
                        user_message_input,
                        send_button,
                    ],
                    spacing=8,
                ),
            ],
            spacing=12,
        ),
    )
