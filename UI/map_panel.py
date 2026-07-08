import flet as ft

def create_map_panel(selected_day_number: int) -> ft.Container:
    """중앙 지도 영역을 만듭니다.

    현재는 실제 Google Maps / Kakao Map / Naver Map을 연결하지 않고,
    지도 자리에 들어갈 UI 골격만 표시합니다.

    나중에는 이 함수 내부를 실제 지도 위젯 또는 WebView 기반 지도 표시로 교체하면 됩니다.
    """

    return ft.Container(
        expand=True,
        padding=24,
        border_radius=16,
        bgcolor="#17202B",
        border=ft.Border.all(1, "#303642"),
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text(
                            "지도 영역",
                            size=22,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Container(expand=True),
                        ft.FilledButton(content=ft.Text("전체 경로")),
                        ft.FilledButton(content=ft.Text(f"Day {selected_day_number}")),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Container(expand=True),
                ft.Text(
                    "Google Maps / Kakao Map / Naver Map 연결 전 플레이스홀더",
                    size=16,
                    color="#B5BECA",
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    "일정 패널을 접으면 지도를 더 넓게 볼 수 있습니다.",
                    size=13,
                    color="#7F8A99",
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(expand=True),
                ft.Row(
                    controls=[
                        ft.FilledButton(content=ft.Text("장소 검색")),
                        ft.FilledButton(content=ft.Text("경로 검증")),
                        ft.FilledButton(content=ft.Text("숙소 보기")),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=10,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )