import flet as ft
from UI.dashboard_view import create_dashboard_view


def main(page: ft.Page) -> None:
    # 앱 창의 제목입니다.
    page.title = "제주 여행 플래너"

    # 전체 앱을 다크 테마로 고정합니다.
    # 현재 UI 색상이 다크 배경 기준으로 구성되어 있기 때문입니다.
    page.theme_mode = ft.ThemeMode.DARK

    # Flet 기본 여백을 없앱니다.
    # 우리가 직접 Header / Body 여백을 제어하기 위함입니다.
    page.padding = 0
    page.bgcolor = "#11151B"

    # 16:9 기준의 기본 창 크기입니다.
    # 1600x900은 1920x1080 모니터에서도 창 모드로 보기 좋고,
    # 지도 + 일정 + Agent 패널을 동시에 배치하기 적당합니다.
    try:
        page.window.width = 1600
        page.window.height = 900
        page.window.min_width = 1280
        page.window.min_height = 720
    except AttributeError:
        # Flet 실행 환경에 따라 window 속성이 없을 수 있어 방어적으로 처리합니다.
        pass

    # 실제 화면 전체를 만드는 함수입니다.
    dashboard_view = create_dashboard_view(page)
    page.controls.clear()
    page.add(dashboard_view)
    page.update()


ft.run(main)