import flet as ft


def create_chat_message(role: str, message: str) -> ft.Container:
    """채팅 메시지 말풍선을 만듭니다.

    role:
        "user" 또는 "agent"를 받습니다.

    message:
        화면에 보여줄 메시지 내용입니다.
    """

    is_user_message = role == "user"

    role_label = "사용자" if is_user_message else "Agent"
    background_color = "#233044" if is_user_message else "#1E252E"
    role_color = "#9CCBFF" if is_user_message else "#B7F5C8"

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
                    color="#E6EAF0",
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
        bgcolor="#20242C",
        content=ft.Text(
            label,
            size=12,
            color="#D6DEE8",
        ),
    )


def create_agent_panel(
    chat_message_list: ft.ListView,
    user_message_input: ft.TextField,
    on_send_message,
) -> ft.Container:
    """오른쪽 Agent 패널 전체를 만듭니다.

    구성:
    1. 제목
    2. Agent가 이해한 조건
    3. 채팅 내역
    4. 하단 입력창

    입력창은 항상 아래에 있어야 사용자가 쉽게 다음 요청을 입력할 수 있습니다.
    """

    understood_conditions = ft.Row(
        controls=[
            create_understood_condition_chip("2박 3일"),
            create_understood_condition_chip("가족"),
            create_understood_condition_chip("렌터카"),
            create_understood_condition_chip("애월 숙소"),
        ],
        wrap=True,
        spacing=8,
        run_spacing=8,
    )

    return ft.Container(
        expand=True,
        padding=16,
        bgcolor="#161A20",
        border_radius=16,
        border=ft.Border.all(1, "#303642"),
        content=ft.Column(
            controls=[
                ft.Text(
                    "제주 여행 Agent",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Text(
                    "자연어로 일정 수정 요청을 입력하세요.",
                    size=12,
                    color="#9AA4B2",
                ),
                ft.Text(
                    "Agent가 이해한 조건",
                    size=13,
                    weight=ft.FontWeight.BOLD,
                ),
                understood_conditions,
                ft.Container(
                    height=1,
                    bgcolor="#303642",
                ),
                chat_message_list,
                ft.Row(
                    controls=[
                        user_message_input,
                        ft.FilledButton(
                            content=ft.Text("전송"),
                            on_click=on_send_message,
                        ),
                    ],
                    spacing=8,
                ),
            ],
            spacing=12,
        ),
    )