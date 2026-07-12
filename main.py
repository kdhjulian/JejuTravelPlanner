import flet as ft
from UI.dashboard_view import create_dashboard_view
from UI.theme import apply_page_theme


def main(page: ft.Page) -> None:
    page.title = "제주 여행 플래너"
    apply_page_theme(page)

    try:
        page.window.width = 1600
        page.window.height = 900
        page.window.min_width = 1280
        page.window.min_height = 720
    except AttributeError:
        pass

    dashboard_view = create_dashboard_view(page)

    page.controls.clear()
    page.add(dashboard_view)
    page.update()


ft.run(main)