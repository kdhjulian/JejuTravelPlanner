import flet as ft

from UI.agent_panel import create_agent_panel, create_chat_message
from UI.itinerary_panel import create_itinerary_panel
from UI.map_panel import create_map_panel


def create_header() -> ft.Container:
    """상단 Header를 만듭니다.

    Header에는 앱 제목과 현재 여행 조건 요약 칩을 배치합니다.
    """

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
      - 왼쪽: 일정 패널, 접기/펼치기 가능
      - 중앙: 지도 패널, 남는 공간을 모두 사용
      - 오른쪽: Agent 패널, 항상 크게 표시

    이 함수가 상태를 들고 있습니다.
    지금은 단순한 dict로 UI 상태를 관리합니다.
    나중에 LangGraph와 연결하면 selected_day, itinerary 같은 값은
    LangGraph State 또는 저장소에서 가져오게 됩니다.
    """

    # 현재 선택된 날짜와 일정 패널 열림 여부를 저장하는 간단한 UI 상태입니다.
    ui_state = {
        "selected_day_number": 1,
    }

    # 이 Container는 왼쪽 일정 패널의 껍데기입니다.
    # 접힘/펼침 상태에 따라 width와 content를 바꿉니다.
    itinerary_shell = ft.Container(
        width=380,
        padding=ft.Padding.only(left=16, top=16, bottom=16),
    )

    # 중앙 지도 패널의 껍데기입니다.
    # selected_day가 바뀌면 content만 다시 교체합니다.
    map_shell = ft.Container(
        expand=True,
        padding=ft.Padding.only(left=16, top=16, bottom=16),
    )

    # Agent 채팅 메시지 목록입니다.
    # ListView는 내용이 많아지면 스크롤됩니다.
    chat_message_list = ft.ListView(
        expand=True,
        spacing=10,
        padding=0,
    )

    # Agent 입력창입니다.
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
        """지도 패널을 현재 선택된 Day 기준으로 다시 그립니다."""

        selected_day_number = ui_state["selected_day_number"]
        map_shell.content = create_map_panel(selected_day_number)

    def refresh_dashboard() -> None:
        """화면 전체를 현재 UI 상태에 맞춰 갱신합니다."""

        refresh_itinerary_panel()
        refresh_map_panel()
        page.update()

    def handle_day_button_click(event: ft.ControlEvent) -> None:
        """Day 1 / Day 2 / Day 3 버튼을 눌렀을 때 실행됩니다."""

        ui_state["selected_day_number"] = int(event.control.data)
        refresh_dashboard()

    def handle_send_message(event: ft.ControlEvent) -> None:
        """Agent 입력창에서 메시지를 보냈을 때 실행됩니다.

        지금은 실제 LangGraph에 연결하지 않고,
        임시 Agent 응답만 추가합니다.

        다음 단계에서는 이 함수 안에서:
        1. 사용자의 자연어 요청을 LangGraph에 전달
        2. LangGraph 결과를 받아 일정 State 갱신
        3. 일정 패널과 지도 패널 갱신
        흐름으로 확장하면 됩니다.
        """

        user_message = user_message_input.value.strip()

        if not user_message:
            return

        chat_message_list.controls.append(
            create_chat_message("user", user_message)
        )

        chat_message_list.controls.append(
            create_chat_message(
                "agent",
                (
                    "아직 LangGraph 연결 전입니다. "
                    "다음 단계에서 이 요청을 그래프에 전달해 "
                    "일정 수정으로 연결합니다."
                ),
            )
        )

        user_message_input.value = ""
        page.update()

    # 사용자가 입력창에서 Enter를 눌러도 전송되게 합니다.
    user_message_input.on_submit = handle_send_message

    # 초기 Agent 안내 메시지입니다.
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

    # 최초 1회 화면 내용을 구성합니다.
    # 이때는 아직 page.add 전이므로 page.update()를 호출하지 않습니다.
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