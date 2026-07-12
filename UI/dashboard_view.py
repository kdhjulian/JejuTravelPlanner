import flet as ft

from Graph.travel_graph import run_travel_agent
from UI.agent_panel import create_agent_panel, create_chat_message
from UI.itinerary_panel import create_itinerary_panel
from UI.map_panel import create_map_panel


def create_header() -> ft.Container:
    """상단 Header를 만듭니다."""

    def create_header_chip(label: str) -> ft.Container:
        return ft.Container(
            padding=ft.Padding.symmetric(horizontal=12, vertical=6),
            border_radius=999,
            bgcolor="#20242C",
            content=ft.Text(label, size=12),
        )

    return ft.Container(
        height=72,
        padding=ft.Padding.symmetric(horizontal=24, vertical=12),
        bgcolor="#11151B",
        content=ft.Row(
            controls=[
                ft.Text(
                    "🏝️ 제주 여행 플래너",
                    size=26,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Container(expand=True),
                create_header_chip("2박 3일"),
                create_header_chip("가족"),
                create_header_chip("렌터카"),
                create_header_chip("애월 숙소"),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
        ),
    )


def create_dashboard_view(page: ft.Page) -> ft.Column:
    """앱의 메인 대시보드 화면을 만듭니다.

    화면 구조:
    Header
    Body Row
      - 왼쪽: 일정 패널
      - 중앙: 지도 패널
      - 오른쪽: Agent 패널
    """

    ui_state = {
        "selected_day_number": 1,
    }

    itinerary_shell = ft.Container(
        width=380,
        padding=ft.Padding.only(left=16, top=16, bottom=16),
    )

    map_shell = ft.Container(
        expand=True,
        padding=ft.Padding.only(left=16, top=16, bottom=16),
    )

    chat_message_list = ft.ListView(
        expand=True,
        spacing=10,
        padding=0,
    )

    user_message_input = ft.TextField(
        hint_text="예: 둘째 날은 애월 중심으로 바꿔줘",
        expand=True,
        border_radius=12,
    )

    def refresh_itinerary_panel() -> None:
        """선택된 Day에 맞춰 왼쪽 일정 패널을 다시 그립니다."""

        selected_day_number = ui_state["selected_day_number"]

        itinerary_shell.content = create_itinerary_panel(
            selected_day_number=selected_day_number,
            on_day_click=handle_day_button_click,
        )

    def refresh_map_panel() -> None:
        """선택된 Day에 맞춰 중앙 지도 패널을 다시 그립니다."""

        selected_day_number = ui_state["selected_day_number"]
        map_shell.content = create_map_panel(selected_day_number)

    def refresh_dashboard() -> None:
        """이미 화면에 올라간 일정/지도 패널을 갱신합니다."""

        refresh_itinerary_panel()
        refresh_map_panel()
        page.update()

    def handle_day_button_click(event: ft.ControlEvent) -> None:
        """Day 1 / Day 2 / Day 3 버튼을 눌렀을 때 실행됩니다."""

        ui_state["selected_day_number"] = int(event.control.data)
        refresh_dashboard()

    def handle_send_message(event: ft.ControlEvent) -> None:
        """Agent 입력창에서 메시지를 보냈을 때 실행됩니다."""

        user_message = user_message_input.value.strip()

        if not user_message:
            return

        chat_message_list.controls.append(
            create_chat_message("user", user_message)
        )

        selected_day_number = ui_state["selected_day_number"]

        try:
            agent_response = run_travel_agent(
                user_message=user_message,
                selected_day_number=selected_day_number,
                destination_name="제주",
            )
        except Exception as error:
            agent_response = (
                "LangGraph 실행 중 오류가 발생했습니다. "
                f"오류 내용: {error}"
            )

        chat_message_list.controls.append(
            create_chat_message("agent", agent_response)
        )

        user_message_input.value = ""
        page.update()

    user_message_input.on_submit = handle_send_message

    chat_message_list.controls.append(
        create_chat_message(
            "agent",
            (
                "안녕하세요. 제주 여행 Agent입니다. "
                "왼쪽에서 일정을 확인하고, 가운데 지도에서 동선을 보면서, "
                "오른쪽에 원하는 수정사항을 입력해 주세요."
            ),
        )
    )

    # 최초 1회 화면 구성.
    # 아직 page.add 전이므로 여기서는 page.update()를 호출하지 않습니다.
    refresh_itinerary_panel()
    refresh_map_panel()

    agent_panel = ft.Container(
        width=420,
        padding=ft.Padding.only(left=16, top=16, right=16, bottom=16),
        content=create_agent_panel(
            chat_message_list=chat_message_list,
            user_message_input=user_message_input,
            on_send_message=handle_send_message,
        ),
    )

    body = ft.Row(
        expand=True,
        spacing=0,
        controls=[
            itinerary_shell,
            map_shell,
            agent_panel,
        ],
    )

    return ft.Column(
        expand=True,
        spacing=0,
        controls=[
            create_header(),
            body,
        ],
    )