"""
main.py — 제주 여행 플래너 앱의 진입점(Entry Point)

Flet 프레임워크를 사용해 데스크톱 GUI 앱을 실행합니다.
페이지 테마를 적용하고, 대시보드 뷰를 생성해 메인 화면에 배치합니다.

실행 방법:
    python main.py
    또는
    flet run main.py
"""

import flet as ft

from UI.dashboard_view import create_dashboard_view
from UI.theme import apply_page_theme


def main(page: ft.Page) -> None:
    """Flet 앱의 메인 함수.

    Flet은 이 함수를 콜백으로 받아, Page 객체를 주입한 뒤 호출합니다.
    Page는 브라우저 탭 또는 데스크톱 윈도우 하나에 대응됩니다.

    Args:
        page: Flet이 생성한 Page 인스턴스. 컨트롤 추가·테마 설정 등 UI 전체를 관리합니다.
    """

    # ── 페이지 기본 설정 ──────────────────────────────────────
    page.title = "제주 여행 플래너"
    apply_page_theme(page)  # theme.py에서 정의한 공통 색상·폰트를 적용

    # ── 윈도우 크기 설정 ──────────────────────────────────────
    # Flet의 데스크톱 모드에서만 동작하는 속성입니다.
    # 웹 모드에서는 window 속성이 없을 수 있으므로 AttributeError를 방어합니다.
    try:
        page.window.width = 1600       # 초기 창 너비(px)
        page.window.height = 900       # 초기 창 높이(px)
        page.window.min_width = 1280   # 최소 창 너비 — 3-패널 레이아웃이 깨지지 않는 하한
        page.window.min_height = 720   # 최소 창 높이
    except AttributeError:
        # 웹 모드에서는 window 속성이 지원되지 않을 수 있으므로 무시합니다.
        pass

    # ── 대시보드 뷰 생성 및 마운트 ─────────────────────────────
    # create_dashboard_view()가 상단 Header + 본문(일정·지도·에이전트) 패널을
    # 포함한 ft.Column을 반환합니다.
    dashboard_view = create_dashboard_view(page)

    # 기존 컨트롤을 모두 제거한 뒤 대시보드 뷰만 추가합니다.
    page.controls.clear()
    page.add(dashboard_view)
    page.update()  # Flet에 렌더링을 요청합니다.


# ── 앱 실행 ──────────────────────────────────────────────────
# ft.run()은 내부적으로 Flet 서버를 기동한 뒤 main()을 호출합니다.
# 데스크톱·웹·모바일 환경에 따라 적절한 런타임을 선택합니다.
ft.run(main)
