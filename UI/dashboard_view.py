import flet as ft

from Graph.travel_graph import run_travel_agent
from UI.agent_panel import create_agent_panel, create_chat_message
from UI.itinerary_panel import create_itinerary_panel
from UI.map_panel import create_map_panel
from UI.theme import (
    HEADER_BACKGROUND_COLOR,
    HEADER_TEXT_COLOR,
    INPUT_BACKGROUND_COLOR,
    INPUT_BORDER_COLOR,
    INPUT_FOCUSED_BORDER_COLOR,
    INPUT_TEXT_COLOR,
    create_condition_chip,
)

def create_header() -> ft.Container:
    """상단 Header를 만듭니다."""

    return ft.Container(
        height=72,
        padding=ft.Padding.symmetric(horizontal=24, vertical=12),
        bgcolor=HEADER_BACKGROUND_COLOR,
        content=ft.Row(
            controls=[
                ft.Text(
                    "🏝️ 제주 여행 플래너",
                    size=26,
                    weight=ft.FontWeight.BOLD,
                    color=HEADER_TEXT_COLOR,
                ),
                ft.Container(expand=True),
                create_condition_chip("2박 3일"),
                create_condition_chip("가족"),
                create_condition_chip("렌터카"),
                create_condition_chip("애월 숙소"),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
        ),
    )


def create_dashboard_view(page: ft.Page) -> ft.Column:
    """앱의 메인 대시보드 화면을 만듭니다."""

    ui_state = {
        "selected_day_number": 1,
        "destination_name": "제주",
        "travel_conditions": [],
        "itinerary_days": [],
    }

    itinerary_shell = ft.Container(
        width=380,
        padding=ft.Padding.only(left=16, top=16, bottom=16),
    )

    map_shell = ft.Container(
        expand=True,
        padding=ft.Padding.only(left=16, top=16, bottom=16),
    )

    agent_shell = ft.Container(
        width=420,
        padding=ft.Padding.only(left=16, top=16, right=16, bottom=16),
    )

    chat_message_list = ft.ListView(
        expand=True,
        spacing=10,
        padding=0,
    )

    user_message_input = ft.TextField(
        hint_text="예: 제주 4박 5일 가족 렌터카 애월 숙소, 카페와 해변 위주",
        expand=True,
        border_radius=12,
        bgcolor=INPUT_BACKGROUND_COLOR,
        color=INPUT_TEXT_COLOR,
        border_color=INPUT_BORDER_COLOR,
        focused_border_color=INPUT_FOCUSED_BORDER_COLOR,
    )

    def refresh_itinerary_panel() -> None:
        """현재 UI 상태에 맞춰 왼쪽 일정 패널을 다시 그립니다."""

        itinerary_shell.content = create_itinerary_panel(
            itinerary_days=ui_state["itinerary_days"],
            selected_day_number=ui_state["selected_day_number"],
            on_day_click=handle_day_button_click,
        )

    def refresh_map_panel() -> None:
        """현재 UI 상태에 맞춰 중앙 지도 패널을 다시 그립니다."""

        map_shell.content = create_map_panel(
            selected_day_number=ui_state["selected_day_number"],
            total_day_count=len(ui_state["itinerary_days"]),
        )

    def refresh_agent_panel() -> None:
        """현재 UI 상태에 맞춰 오른쪽 여행 도우미 패널을 다시 그립니다."""

        agent_shell.content = create_agent_panel(
            chat_message_list=chat_message_list,
            user_message_input=user_message_input,
            on_send_message=handle_send_message,
            travel_condition_chips=ui_state["travel_conditions"],
        )

    def refresh_dashboard(should_update_page: bool = True) -> None:
        """화면 전체를 현재 UI 상태에 맞춰 갱신합니다."""

        refresh_itinerary_panel()
        refresh_map_panel()
        refresh_agent_panel()

        if should_update_page:
            page.update()

    def handle_day_button_click(event: ft.ControlEvent) -> None:
        """Day 버튼을 눌렀을 때 선택 Day를 변경합니다."""

        ui_state["selected_day_number"] = int(event.control.data)
        refresh_dashboard()

    def handle_send_message(event: ft.ControlEvent) -> None:
        """여행 도우미 입력창에서 메시지를 보냈을 때 실행됩니다."""

        user_message = user_message_input.value.strip()

        if not user_message:
            return

        chat_message_list.controls.append(
            create_chat_message("user", user_message)
        )

        try:
            agent_result = run_travel_agent(
                user_message=user_message,
                selected_day_number=ui_state["selected_day_number"],
                destination_name=ui_state.get("destination_name", ""),
                travel_conditions=ui_state["travel_conditions"],
                itinerary_days=ui_state["itinerary_days"],
                trip_day_count=ui_state.get("trip_day_count"),
            )

            ui_state["destination_name"] = agent_result.get(
                "destination_name",
                ui_state.get("destination_name", ""),
            )

            if "trip_day_count" in agent_result:
                ui_state["trip_day_count"] = agent_result["trip_day_count"]

            if "travel_conditions" in agent_result:
                ui_state["travel_conditions"] = agent_result["travel_conditions"]

            if "itinerary_days" in agent_result:
                ui_state["itinerary_days"] = agent_result["itinerary_days"]
                ui_state["selected_day_number"] = 1

            if "target_day_number" in agent_result:
                target_day_number = agent_result["target_day_number"]
                total_day_count = len(ui_state["itinerary_days"])

                if 1 <= target_day_number <= total_day_count:
                    ui_state["selected_day_number"] = target_day_number

            agent_response = agent_result.get(
                "agent_response",
                "요청을 확인했습니다.",
            )

        except Exception as error:
            agent_response = (
                "LangGraph 실행 중 오류가 발생했습니다. "
                f"오류 내용: {error}"
            )

        chat_message_list.controls.append(
            create_chat_message("assistant", agent_response)
        )

        user_message_input.value = ""
        refresh_dashboard()

    user_message_input.on_submit = handle_send_message

    refresh_dashboard(should_update_page=False)

    body = ft.Row(
        expand=True,
        spacing=0,
        controls=[
            itinerary_shell,
            map_shell,
            agent_shell,
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