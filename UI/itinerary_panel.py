import flet as ft


# 아직 실제 LangGraph / Google Places API를 연결하지 않았으므로,
# UI 동작 확인용 샘플 일정 데이터를 사용합니다.
#
# 구조:
# {
#   Day 번호: [
#       {
#           "time": 시간,
#           "title": 장소 또는 활동명,
#           "description": 설명,
#           "travel_time": 이전 장소에서 이동시간
#       }
#   ]
# }
SAMPLE_ITINERARIES: dict[int, list[dict[str, str]]] = {
    1: [
        {
            "time": "10:00",
            "title": "제주공항 도착",
            "description": "렌터카 수령 후 애월 방향으로 이동",
            "travel_time": "이동 35분",
        },
        {
            "time": "11:30",
            "title": "애월 브런치",
            "description": "바다 근처 브런치 카페에서 여행 시작",
            "travel_time": "이동 10분",
        },
        {
            "time": "13:30",
            "title": "곽지해수욕장",
            "description": "가볍게 산책하고 사진 촬영",
            "travel_time": "이동 20분",
        },
        {
            "time": "16:00",
            "title": "오션뷰 카페",
            "description": "느긋하게 쉬는 카페 일정",
            "travel_time": "이동 15분",
        },
        {
            "time": "18:30",
            "title": "애월 숙소 체크인",
            "description": "숙소 체크인 후 휴식",
            "travel_time": "이동 10분",
        },
    ],
    2: [
        {
            "time": "09:30",
            "title": "협재해수욕장",
            "description": "서쪽 바다 중심 일정",
            "travel_time": "이동 25분",
        },
        {
            "time": "11:30",
            "title": "한림 점심",
            "description": "현지 음식점 후보 방문",
            "travel_time": "이동 15분",
        },
        {
            "time": "14:00",
            "title": "금능해변",
            "description": "협재와 가까운 해변 코스",
            "travel_time": "이동 10분",
        },
        {
            "time": "17:00",
            "title": "숙소 복귀",
            "description": "무리하지 않는 여유 일정",
            "travel_time": "이동 30분",
        },
    ],
    3: [
        {
            "time": "09:00",
            "title": "숙소 체크아웃",
            "description": "짐 정리 후 제주시 방향 이동",
            "travel_time": "이동 40분",
        },
        {
            "time": "10:30",
            "title": "제주시 카페",
            "description": "공항 근처에서 마지막 휴식",
            "travel_time": "이동 20분",
        },
        {
            "time": "12:30",
            "title": "공항 근처 점심",
            "description": "비행 전 가벼운 식사",
            "travel_time": "이동 15분",
        },
        {
            "time": "14:00",
            "title": "제주공항 도착",
            "description": "렌터카 반납 후 출발 준비",
            "travel_time": "일정 종료",
        },
    ],
}


def create_day_button(
    day_number: int,
    selected_day_number: int,
    on_day_click,
) -> ft.FilledButton:
    """Day 1, Day 2, Day 3 버튼을 만듭니다.

    day_number:
        이 버튼이 의미하는 날짜 번호입니다.

    selected_day_number:
        현재 선택된 날짜 번호입니다.

    on_day_click:
        버튼을 눌렀을 때 dashboard_view.py에서 실행할 함수입니다.

    버튼의 data 속성에 day_number를 저장해두면,
    클릭 이벤트에서 event.control.data로 어떤 날짜를 눌렀는지 알 수 있습니다.
    """

    is_selected = day_number == selected_day_number
    label = f"Day {day_number}"

    if is_selected:
        label = f"✓ {label}"

    return ft.FilledButton(
        content=ft.Text(label),
        data=day_number,
        on_click=on_day_click,
    )


def create_itinerary_card(schedule_item: dict[str, str]) -> ft.Container:
    """일정 카드 하나를 만듭니다.

    예:
    10:00 제주공항 도착
    렌터카 수령 후 애월 방향으로 이동
    [위로] [아래로] [삭제] [고정]

    지금은 버튼을 눌러도 실제 순서 변경은 하지 않습니다.
    다음 단계에서 on_click을 연결해 실제 일정 변경 기능을 붙입니다.
    """

    return ft.Container(
        padding=12,
        border_radius=14,
        bgcolor="#20242C",
        border=ft.Border.all(1, "#343A46"),
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text(
                            schedule_item["time"],
                            size=14,
                            weight=ft.FontWeight.BOLD,
                            color="#9CCBFF",
                        ),
                        ft.Container(expand=True),
                        ft.Text(
                            schedule_item["travel_time"],
                            size=12,
                            color="#9AA4B2",
                        ),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Text(
                    schedule_item["title"],
                    size=17,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Text(
                    schedule_item["description"],
                    size=13,
                    color="#B5BECA",
                ),
                ft.Row(
                    controls=[
                        ft.Container(
                            width=50,
                            height=28,
                            border_radius=14,
                            bgcolor="#9CCBFF",
                            alignment=ft.Alignment.CENTER,
                            content=ft.Text("위로", size=14, color="#0F1720"),
                            tooltip="위로 이동",
                            on_click=lambda event: None,
                        ),
                        ft.Container(
                            width=50,
                            height=28,
                            border_radius=14,
                            bgcolor="#9CCBFF",
                            alignment=ft.Alignment.CENTER,
                            content=ft.Text("아래로", size=14, color="#0F1720"),
                            tooltip="아래로 이동",
                            on_click=lambda event: None,
                        ),
                        ft.Container(
                            width=50,
                            height=28,
                            border_radius=14,
                            bgcolor="#9CCBFF",
                            alignment=ft.Alignment.CENTER,
                            content=ft.Text("삭제", size=14, color="#0F1720"),
                            tooltip="삭제",
                            on_click=lambda event: None,
                        ),
                        ft.Container(
                            width=50,
                            height=28,
                            border_radius=14,
                            bgcolor="#9CCBFF",
                            alignment=ft.Alignment.CENTER,
                            content=ft.Text("고정", size=14, color="#0F1720"),
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


def build_itinerary_cards(day_number: int) -> list[ft.Control]:
    """선택된 Day 번호에 맞는 일정 카드 목록을 만듭니다."""

    schedule_items = SAMPLE_ITINERARIES.get(day_number, [])

    return [
        create_itinerary_card(schedule_item)
        for schedule_item in schedule_items
    ]


def create_itinerary_panel(
    selected_day_number: int,
    on_day_click,
) -> ft.Container:
    """왼쪽 고정 일정 패널을 만듭니다.

    접기/펼치기 없이 항상 화면 왼쪽에 표시합니다.
    지도와 일정을 동시에 보기 위한 구조입니다.
    """

    itinerary_list = ft.ListView(
        expand=True,
        spacing=10,
        padding=0,
        controls=build_itinerary_cards(selected_day_number),
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
                    f"Day {selected_day_number} 일정",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Row(
                    controls=[
                        create_day_button(1, selected_day_number, on_day_click),
                        create_day_button(2, selected_day_number, on_day_click),
                        create_day_button(3, selected_day_number, on_day_click),
                    ],
                    spacing=8,
                ),
                itinerary_list,
            ],
            spacing=12,
        ),
    )
