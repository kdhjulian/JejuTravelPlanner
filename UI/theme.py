"""
UI/theme.py — 앱 전역 테마(색상·폰트·공통 컴포넌트)

이 파일은 세 가지 역할을 합니다:
    1. 색상 팔레트 정의 — 기본 4색 + 파생 색상 + 시맨틱(역할 기반) 색상
    2. 공통 Border·Divider·Button·Chip 팩토리 함수
    3. Page 테마 적용 헬퍼

색상 계층 구조:
    Base Colors (4색) → Derived Colors (가독성·세부 역할) → Semantic Colors (UI 역할 이름)

    UI 파일에서는 Semantic Colors를 사용해, 색상 변경 시 이 파일만 수정하면 됩니다.
"""

import flet as ft


# ============================================================
# Font
# ============================================================
# Windows 기본 한글 글꼴인 "맑은 고딕"을 우선 사용합니다.
# macOS, Linux 등에서는 Flet이 시스템 기본 글꼴로 자동 fallback합니다.
# ============================================================
APP_FONT_FAMILY = "Malgun Gothic"


# ============================================================
# Base Theme Colors (기본 4색 팔레트)
# ============================================================
# 따뜻한 파스텔(warm pastel) 계열 테마입니다.
#
# RGB 참고:
#   255, 237, 168 → #FFEDA8 (밝은 노란색 — 하이라이트/활성 상태)
#   249, 189, 143 → #F9BD8F (살구색 — 버튼/헤더)
#   248, 221, 222 → #F8DDDE (연분홍 — 패널 배경/카드 영역)
#   254, 244, 238 → #FEF4EE (아이보리 — 전체 배경)
# ============================================================
BACKGROUND_COLOR = "#FEF4EE"    # 전체 배경 — 가장 밝은 아이보리
CARD_COLOR = "#F8DDDE"          # 패널/카드 영역 배경 — 연분홍
BUTTON_COLOR = "#F9BD8F"        # 버튼 기본 색상 — 살구색
HIGHLIGHT_COLOR = "#FFEDA8"     # 활성/선택 상태 — 밝은 노란색


# ============================================================
# Derived Colors (파생 색상)
# ============================================================
# 밝은 파스텔 위에서 가독성을 확보하기 위한 진한 텍스트/테두리 색상입니다.
# Base Color에서 직접 사용하기 어려운 역할(텍스트, 테두리, 시간 표시 등)을
# 별도로 정의합니다.
# ============================================================

# 텍스트 색상 — 파스텔 배경과 충분한 대비를 확보
DARK_TEXT_COLOR = "#4A2F2A"     # 진한 갈색 — 제목·본문 텍스트
MUTED_TEXT_COLOR = "#7C5F57"    # 회갈색 — 부연 설명·비활성 텍스트

# 헤더 색상
HEADER_COLOR = "#F9BD8F"        # 살구색 — 헤더 배경
HEADER_TEXT_COLOR = "#4A2F2A"   # 진한 갈색 — 헤더 텍스트

# 카드 내부·배경 변형
SOFT_CARD_COLOR = "#FFF1EC"     # 카드 내부 배경 (CARD_COLOR보다 밝음)
SOFT_BACKGROUND_COLOR = "#FFF7F2"  # 입력창 등 부드러운 배경

# 테두리 색상
BORDER_COLOR = "#E0A58F"        # 주요 테두리 — 패널, 구분선
SOFT_BORDER_COLOR = "#EFC5BE"   # 연한 테두리 — 카드 개별 테두리

# 강조(Accent) 색상
ACCENT_COLOR = "#FFEDA8"        # 약한 강조 — 하이라이트 색상 재활용
ACCENT_STRONG_COLOR = "#D98253" # 강한 강조 — 활성 테두리, 에이전트 라벨

# 일정 카드 전용 색상
TIME_TEXT_COLOR = "#B25F32"     # 시간 표시 (주황 계열)
TRAVEL_TIME_TEXT_COLOR = "#7C5F57"  # 이동 시간 표시 (회갈색)

# 비활성 상태
DISABLED_COLOR = "#F3D8D4"     # 비활성 요소 배경 (현재 미사용, 확장용)


# ============================================================
# Semantic Theme Colors (시맨틱/역할 기반 색상)
# ============================================================
# UI 파일에서는 가능하면 이 역할 기반 이름을 사용합니다.
# 예: PANEL_BACKGROUND_COLOR 대신 CARD_COLOR을 직접 쓰지 않습니다.
# 이렇게 하면 색상 변경 시 의미 단위로 일괄 수정이 가능합니다.
# ============================================================

APP_BACKGROUND_COLOR = BACKGROUND_COLOR          # 페이지 전체 배경
HEADER_BACKGROUND_COLOR = HEADER_COLOR           # 상단 헤더 배경

PANEL_BACKGROUND_COLOR = CARD_COLOR              # 3-패널 각각의 배경
CARD_BACKGROUND_COLOR = SOFT_CARD_COLOR          # 패널 안의 카드 배경
MAP_BACKGROUND_COLOR = CARD_COLOR                # 지도 패널 배경

PRIMARY_TEXT_COLOR = DARK_TEXT_COLOR              # 제목·주요 텍스트
SECONDARY_TEXT_COLOR = MUTED_TEXT_COLOR           # 설명·부연 텍스트
LIGHT_TEXT_COLOR = SOFT_BACKGROUND_COLOR          # 어두운 배경 위 밝은 텍스트 (현재 미사용)

DIVIDER_COLOR = BORDER_COLOR                     # 패널 내부 구분선

# 비활성(선택되지 않은) 버튼
INACTIVE_BUTTON_BACKGROUND_COLOR = BUTTON_COLOR
INACTIVE_BUTTON_TEXT_COLOR = DARK_TEXT_COLOR
INACTIVE_BUTTON_BORDER_COLOR = ACCENT_STRONG_COLOR

# 활성(선택된) 버튼
ACTIVE_BUTTON_BACKGROUND_COLOR = HIGHLIGHT_COLOR
ACTIVE_BUTTON_TEXT_COLOR = DARK_TEXT_COLOR
ACTIVE_BUTTON_BORDER_COLOR = ACCENT_STRONG_COLOR

# 주요 액션 버튼 (전송 버튼 등)
PRIMARY_ACTION_BACKGROUND_COLOR = HIGHLIGHT_COLOR
PRIMARY_ACTION_TEXT_COLOR = DARK_TEXT_COLOR
PRIMARY_ACTION_BORDER_COLOR = ACCENT_STRONG_COLOR

# 조건 칩(Condition Chip)
CONDITION_CHIP_BACKGROUND_COLOR = HIGHLIGHT_COLOR
CONDITION_CHIP_TEXT_COLOR = DARK_TEXT_COLOR
CONDITION_CHIP_BORDER_COLOR = ACCENT_STRONG_COLOR

# 채팅 말풍선 — 사용자
USER_MESSAGE_BACKGROUND_COLOR = BUTTON_COLOR
USER_MESSAGE_TEXT_COLOR = DARK_TEXT_COLOR

# 채팅 말풍선 — 에이전트
AGENT_MESSAGE_BACKGROUND_COLOR = SOFT_CARD_COLOR
AGENT_MESSAGE_TEXT_COLOR = DARK_TEXT_COLOR

# 텍스트 입력창
INPUT_BACKGROUND_COLOR = SOFT_BACKGROUND_COLOR
INPUT_TEXT_COLOR = DARK_TEXT_COLOR
INPUT_HINT_TEXT_COLOR = MUTED_TEXT_COLOR          # 힌트 텍스트 (Flet 기본 적용)
INPUT_BORDER_COLOR = BORDER_COLOR
INPUT_FOCUSED_BORDER_COLOR = ACCENT_STRONG_COLOR


# ============================================================
# Page Theme Helper
# ============================================================
def apply_page_theme(page: ft.Page) -> None:
    """앱 전체 Page에 공통 테마를 적용합니다.

    main.py에서 Page 생성 직후 호출됩니다.

    Args:
        page: Flet Page 인스턴스.
    """

    page.theme_mode = ft.ThemeMode.LIGHT   # 라이트 모드 고정
    page.bgcolor = APP_BACKGROUND_COLOR    # 페이지 배경색
    page.padding = 0                       # 기본 패딩 제거 (레이아웃에서 직접 관리)

    # Flet 버전에 따라 Theme 객체 지원 여부가 다를 수 있으므로 방어합니다.
    try:
        page.theme = ft.Theme(font_family=APP_FONT_FAMILY)
    except (AttributeError, TypeError):
        pass


# ============================================================
# Border Helpers — 일관된 테두리 생성
# ============================================================
def create_panel_border() -> ft.Border:
    """공통 패널 테두리를 만듭니다.

    3-패널(일정·지도·에이전트) 외곽에 사용됩니다.

    Returns:
        ft.Border — 1px BORDER_COLOR 테두리.
    """

    return ft.Border.all(1, BORDER_COLOR)


def create_card_border() -> ft.Border:
    """카드에 사용할 공통 테두리를 만듭니다.

    패널 안의 개별 카드(일정 카드, 동선 카드 등)에 사용됩니다.
    패널 테두리보다 연한 색상으로 시각적 계층을 만듭니다.

    Returns:
        ft.Border — 1px SOFT_BORDER_COLOR 테두리.
    """

    return ft.Border.all(1, SOFT_BORDER_COLOR)


def create_button_border(is_selected: bool = False) -> ft.Border:
    """버튼 선택 상태에 맞는 테두리를 만듭니다.

    Args:
        is_selected: True이면 활성 상태 테두리, False이면 비활성 상태 테두리.

    Returns:
        ft.Border — 선택 상태에 따른 1px 테두리.
    """

    border_color = (
        ACTIVE_BUTTON_BORDER_COLOR
        if is_selected
        else INACTIVE_BUTTON_BORDER_COLOR
    )

    return ft.Border.all(1, border_color)


# ============================================================
# Common Controls — 재사용 가능한 UI 컴포넌트 팩토리
# ============================================================
def create_divider() -> ft.Container:
    """패널 내부 구분선을 만듭니다.

    Flet의 ft.Divider() 대신 1px 높이의 Container를 사용하여
    색상을 직접 제어합니다.

    Returns:
        ft.Container — 1px 높이의 수평 구분선.
    """

    return ft.Container(
        height=1,
        bgcolor=DIVIDER_COLOR,
    )


def create_pill_button(
    label: str,
    is_selected: bool = False,
    width: int | None = None,
    height: int = 34,
    on_click=None,
    data=None,
    tooltip: str | None = None,
) -> ft.Container:
    """둥근 pill 형태 버튼을 만듭니다.

    Day 선택 버튼, 일정 카드 액션 버튼(위/아래/삭제/고정) 등에 사용됩니다.
    border_radius를 height의 절반으로 설정해 완전한 라운드 모서리를 만듭니다.

    Args:
        label:       버튼 텍스트.
        is_selected: True이면 활성 색상, False이면 비활성 색상 적용.
        width:       고정 너비. None이면 텍스트 크기에 맞춤.
        height:      버튼 높이 (기본 34px).
        on_click:    클릭 이벤트 핸들러 (ft.ControlEvent → None).
        data:        이벤트 핸들러에 전달할 사용자 데이터.
        tooltip:     마우스 오버 시 표시할 툴팁 텍스트.

    Returns:
        ft.Container — 클릭 가능한 pill 버튼 컨테이너.
    """

    # 선택 상태에 따라 배경색·텍스트 색상 분기
    background_color = (
        ACTIVE_BUTTON_BACKGROUND_COLOR
        if is_selected
        else INACTIVE_BUTTON_BACKGROUND_COLOR
    )

    text_color = (
        ACTIVE_BUTTON_TEXT_COLOR
        if is_selected
        else INACTIVE_BUTTON_TEXT_COLOR
    )

    return ft.Container(
        width=width,
        height=height,
        padding=ft.Padding.symmetric(horizontal=12, vertical=0),
        border_radius=height // 2,   # 높이의 절반 → 완전한 pill 모양
        bgcolor=background_color,
        border=create_button_border(is_selected),
        alignment=ft.Alignment.CENTER,
        data=data,
        tooltip=tooltip,
        on_click=on_click,
        content=ft.Text(
            label,
            size=13,
            weight=ft.FontWeight.BOLD,
            color=text_color,
        ),
    )


def create_primary_button(
    label: str,
    width: int | None = None,
    height: int = 34,
    on_click=None,
    data=None,
    tooltip: str | None = None,
) -> ft.Container:
    """주요 액션 버튼을 만듭니다.

    에이전트 패널의 "전송" 버튼 등 핵심 액션에 사용됩니다.
    pill_button과 유사하지만 항상 활성(하이라이트) 색상을 사용합니다.

    Args:
        label:    버튼 텍스트.
        width:    고정 너비.
        height:   버튼 높이.
        on_click: 클릭 이벤트 핸들러.
        data:     이벤트 핸들러에 전달할 데이터.
        tooltip:  툴팁 텍스트.

    Returns:
        ft.Container — 클릭 가능한 주요 액션 버튼.
    """

    return ft.Container(
        width=width,
        height=height,
        padding=ft.Padding.symmetric(horizontal=12, vertical=0),
        border_radius=height // 2,
        bgcolor=PRIMARY_ACTION_BACKGROUND_COLOR,
        border=ft.Border.all(1, PRIMARY_ACTION_BORDER_COLOR),
        alignment=ft.Alignment.CENTER,
        data=data,
        tooltip=tooltip,
        on_click=on_click,
        content=ft.Text(
            label,
            size=13,
            weight=ft.FontWeight.BOLD,
            color=PRIMARY_ACTION_TEXT_COLOR,
        ),
    )


def create_condition_chip(label: str) -> ft.Container:
    """여행 조건 표시용 작은 칩(Chip)을 만듭니다.

    헤더의 "제주 전용" 칩, 에이전트 패널의 여행 조건 칩 등에 사용됩니다.
    border_radius=999로 완전한 캡슐 형태를 만듭니다.

    Args:
        label: 칩에 표시할 텍스트 (예: "부모님 동반", "렌터카").

    Returns:
        ft.Container — 캡슐형 조건 칩.
    """

    return ft.Container(
        padding=ft.Padding.symmetric(horizontal=10, vertical=6),
        border_radius=999,  # 매우 큰 값 → 어떤 크기에서도 완전한 캡슐
        bgcolor=CONDITION_CHIP_BACKGROUND_COLOR,
        border=ft.Border.all(1, CONDITION_CHIP_BORDER_COLOR),
        content=ft.Text(
            label,
            size=12,
            weight=ft.FontWeight.BOLD,
            color=CONDITION_CHIP_TEXT_COLOR,
        ),
    )
