import flet as ft

from Graph.travel_graph import run_travel_agent
from UI.agent_panel import create_agent_panel, create_chat_message, create_typing_indicator
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
from app_config import (
    APP_SCOPE_LABEL,
    APP_TITLE,
    DEFAULT_TRAVEL_CONDITION,
    SUPPORTED_DESTINATION_NAME,
    TRAVEL_INPUT_HINT_TEXT,
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
                    APP_TITLE,
                    size=26,
                    weight=ft.FontWeight.BOLD,
                    color=HEADER_TEXT_COLOR,
                ),
                ft.Container(expand=True),
                create_condition_chip(APP_SCOPE_LABEL),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
        ),
    )


def create_dashboard_view(page: ft.Page) -> ft.Column:
    """앱의 메인 대시보드 화면을 만듭니다."""

    ui_state = {
        "selected_day_number": 1,
        "destination_name": SUPPORTED_DESTINATION_NAME,
        "travel_conditions": [DEFAULT_TRAVEL_CONDITION.copy()],
        "itinerary_days": [],
        "trip_day_count": None,
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
        hint_text=TRAVEL_INPUT_HINT_TEXT,
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
            on_move_item_up=handle_move_item_up,
            on_move_item_down=handle_move_item_down,
            on_delete_item=handle_delete_item,
            on_toggle_fixed_item=handle_toggle_fixed_item,
        )

    def refresh_map_panel() -> None:
        """현재 UI 상태에 맞춰 중앙 지도 패널을 다시 그립니다."""

        map_shell.content = create_map_panel(
            selected_day_number=ui_state["selected_day_number"],
            itinerary_days=ui_state["itinerary_days"],
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

    def find_itinerary_day(day_number: int) -> dict | None:
        """현재 UI State에서 특정 Day 데이터를 찾습니다."""

        for itinerary_day in ui_state["itinerary_days"]:
            if itinerary_day["day_number"] == day_number:
                return itinerary_day

        return None


    def find_item_index(items: list[dict], item_id: str) -> int | None:
        """특정 item_id를 가진 카드의 index를 찾습니다."""

        for item_index, item in enumerate(items):
            if item.get("item_id") == item_id:
                return item_index

        return None


    def handle_move_item_up(event: ft.ControlEvent) -> None:
        """카드를 같은 Day 안에서 한 칸 위로 이동합니다."""

        event_data = event.control.data
        day_number = event_data["day_number"]
        item_id = event_data["item_id"]

        itinerary_day = find_itinerary_day(day_number)

        if itinerary_day is None:
            return

        items = itinerary_day.get("items", [])
        item_index = find_item_index(items, item_id)

        if item_index is None or item_index <= 0:
            return

        items[item_index - 1], items[item_index] = (
            items[item_index],
            items[item_index - 1],
        )

        refresh_dashboard()


    def handle_move_item_down(event: ft.ControlEvent) -> None:
        """카드를 같은 Day 안에서 한 칸 아래로 이동합니다."""

        event_data = event.control.data
        day_number = event_data["day_number"]
        item_id = event_data["item_id"]

        itinerary_day = find_itinerary_day(day_number)

        if itinerary_day is None:
            return

        items = itinerary_day.get("items", [])
        item_index = find_item_index(items, item_id)

        if item_index is None or item_index >= len(items) - 1:
            return

        items[item_index], items[item_index + 1] = (
            items[item_index + 1],
            items[item_index],
        )

        refresh_dashboard()


    def handle_delete_item(event: ft.ControlEvent) -> None:
        """카드를 삭제합니다."""

        event_data = event.control.data
        day_number = event_data["day_number"]
        item_id = event_data["item_id"]

        itinerary_day = find_itinerary_day(day_number)

        if itinerary_day is None:
            return

        itinerary_day["items"] = [
            item
            for item in itinerary_day.get("items", [])
            if item.get("item_id") != item_id
        ]

        refresh_dashboard()


    def handle_toggle_fixed_item(event: ft.ControlEvent) -> None:
        """카드 고정 상태를 토글합니다."""

        event_data = event.control.data
        day_number = event_data["day_number"]
        item_id = event_data["item_id"]

        itinerary_day = find_itinerary_day(day_number)

        if itinerary_day is None:
            return

        for item in itinerary_day.get("items", []):
            if item.get("item_id") == item_id:
                item["is_fixed"] = not item.get("is_fixed", False)
                break

        refresh_dashboard()

    def handle_send_message(event: ft.ControlEvent) -> None:
        """여행 도우미 입력창에서 메시지를 보냈을 때 실행됩니다."""

        user_message = user_message_input.value.strip()

        if not user_message:
            return

        # ── 1) 사용자 메시지를 즉시 화면에 표시 ──
        chat_message_list.controls.append(
            create_chat_message("user", user_message)
        )
        user_message_input.value = ""

        # ── 2) 타이핑 인디케이터 표시 ──
        typing_indicator = create_typing_indicator()
        chat_message_list.controls.append(typing_indicator)
        page.update()

        # ── 3) LLM 에이전트 호출 (동기 블로킹) ──
        try:
            agent_result = run_travel_agent(
                user_message=user_message,
                selected_day_number=ui_state["selected_day_number"],
                destination_name=SUPPORTED_DESTINATION_NAME,
                travel_conditions=ui_state["travel_conditions"],
                itinerary_days=ui_state["itinerary_days"],
                trip_day_count=ui_state["trip_day_count"],
            )

            ui_state["destination_name"] = SUPPORTED_DESTINATION_NAME

            if "trip_day_count" in agent_result:
                ui_state["trip_day_count"] = agent_result["trip_day_count"]

            if "travel_conditions" in agent_result:
                ui_state["travel_conditions"] = agent_result["travel_conditions"]

            if "itinerary_days" in agent_result:
                ui_state["itinerary_days"] = agent_result["itinerary_days"]

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

        # ── 4) 타이핑 인디케이터 제거 → 에이전트 응답 표시 ──
        chat_message_list.controls.remove(typing_indicator)
        chat_message_list.controls.append(
            create_chat_message("agent", agent_response)
        )

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