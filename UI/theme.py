import flet as ft


# ============================================================
# Font
# ============================================================
# Windows 기본 한글 글꼴인 맑은 고딕을 우선 사용합니다.
# 다른 OS에서는 시스템 기본 글꼴로 fallback됩니다.
# ============================================================

APP_FONT_FAMILY = "Malgun Gothic"


# ============================================================
# Base Theme Colors
# ============================================================
# Warm pastel theme
#
# 255, 237, 168 → #FFEDA8
# 249, 189, 143 → #F9BD8F
# 248, 221, 222 → #F8DDDE
# 254, 244, 238 → #FEF4EE
# ============================================================

BACKGROUND_COLOR = "#FEF4EE"
CARD_COLOR = "#F8DDDE"
BUTTON_COLOR = "#F9BD8F"
HIGHLIGHT_COLOR = "#FFEDA8"


# ============================================================
# Derived Colors
# ============================================================
# 밝은 파스텔 위에서 가독성을 확보하기 위한 진한 텍스트/테두리 색상입니다.
# ============================================================

DARK_TEXT_COLOR = "#4A2F2A"
MUTED_TEXT_COLOR = "#7C5F57"

HEADER_COLOR = "#F9BD8F"
HEADER_TEXT_COLOR = "#4A2F2A"

SOFT_CARD_COLOR = "#FFF1EC"
SOFT_BACKGROUND_COLOR = "#FFF7F2"

BORDER_COLOR = "#E0A58F"
SOFT_BORDER_COLOR = "#EFC5BE"

ACCENT_COLOR = "#FFEDA8"
ACCENT_STRONG_COLOR = "#D98253"

TIME_TEXT_COLOR = "#B25F32"
TRAVEL_TIME_TEXT_COLOR = "#7C5F57"

DISABLED_COLOR = "#F3D8D4"


# ============================================================
# Semantic Theme Colors
# ============================================================
# UI 파일에서는 가능하면 이 역할 기반 이름을 사용합니다.
# ============================================================

APP_BACKGROUND_COLOR = BACKGROUND_COLOR
HEADER_BACKGROUND_COLOR = HEADER_COLOR

PANEL_BACKGROUND_COLOR = CARD_COLOR
CARD_BACKGROUND_COLOR = SOFT_CARD_COLOR
MAP_BACKGROUND_COLOR = CARD_COLOR

PRIMARY_TEXT_COLOR = DARK_TEXT_COLOR
SECONDARY_TEXT_COLOR = MUTED_TEXT_COLOR
LIGHT_TEXT_COLOR = SOFT_BACKGROUND_COLOR

DIVIDER_COLOR = BORDER_COLOR

INACTIVE_BUTTON_BACKGROUND_COLOR = BUTTON_COLOR
INACTIVE_BUTTON_TEXT_COLOR = DARK_TEXT_COLOR
INACTIVE_BUTTON_BORDER_COLOR = ACCENT_STRONG_COLOR

ACTIVE_BUTTON_BACKGROUND_COLOR = HIGHLIGHT_COLOR
ACTIVE_BUTTON_TEXT_COLOR = DARK_TEXT_COLOR
ACTIVE_BUTTON_BORDER_COLOR = ACCENT_STRONG_COLOR

PRIMARY_ACTION_BACKGROUND_COLOR = HIGHLIGHT_COLOR
PRIMARY_ACTION_TEXT_COLOR = DARK_TEXT_COLOR
PRIMARY_ACTION_BORDER_COLOR = ACCENT_STRONG_COLOR

CONDITION_CHIP_BACKGROUND_COLOR = HIGHLIGHT_COLOR
CONDITION_CHIP_TEXT_COLOR = DARK_TEXT_COLOR
CONDITION_CHIP_BORDER_COLOR = ACCENT_STRONG_COLOR

USER_MESSAGE_BACKGROUND_COLOR = BUTTON_COLOR
USER_MESSAGE_TEXT_COLOR = DARK_TEXT_COLOR

AGENT_MESSAGE_BACKGROUND_COLOR = SOFT_CARD_COLOR
AGENT_MESSAGE_TEXT_COLOR = DARK_TEXT_COLOR

INPUT_BACKGROUND_COLOR = SOFT_BACKGROUND_COLOR
INPUT_TEXT_COLOR = DARK_TEXT_COLOR
INPUT_HINT_TEXT_COLOR = MUTED_TEXT_COLOR
INPUT_BORDER_COLOR = BORDER_COLOR
INPUT_FOCUSED_BORDER_COLOR = ACCENT_STRONG_COLOR


# ============================================================
# Page Theme Helper
# ============================================================

def apply_page_theme(page: ft.Page) -> None:
    """앱 전체 Page에 공통 테마를 적용합니다."""

    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = APP_BACKGROUND_COLOR
    page.padding = 0

    try:
        page.theme = ft.Theme(font_family=APP_FONT_FAMILY)
    except (AttributeError, TypeError):
        pass


# ============================================================
# Border Helpers
# ============================================================

def create_panel_border() -> ft.Border:
    """공통 패널 테두리를 만듭니다."""

    return ft.Border.all(1, BORDER_COLOR)


def create_card_border() -> ft.Border:
    """카드에 사용할 공통 테두리를 만듭니다."""

    return ft.Border.all(1, SOFT_BORDER_COLOR)


def create_button_border(is_selected: bool = False) -> ft.Border:
    """버튼 선택 상태에 맞는 테두리를 만듭니다."""

    border_color = (
        ACTIVE_BUTTON_BORDER_COLOR
        if is_selected
        else INACTIVE_BUTTON_BORDER_COLOR
    )

    return ft.Border.all(1, border_color)


# ============================================================
# Common Controls
# ============================================================

def create_divider() -> ft.Container:
    """패널 내부 구분선을 만듭니다."""

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
    """둥근 pill 형태 버튼을 만듭니다."""

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
        border_radius=height // 2,
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
    """주요 액션 버튼을 만듭니다."""

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
    """여행 조건 표시용 작은 칩을 만듭니다."""

    return ft.Container(
        padding=ft.Padding.symmetric(horizontal=10, vertical=6),
        border_radius=999,
        bgcolor=CONDITION_CHIP_BACKGROUND_COLOR,
        border=ft.Border.all(1, CONDITION_CHIP_BORDER_COLOR),
        content=ft.Text(
            label,
            size=12,
            weight=ft.FontWeight.BOLD,
            color=CONDITION_CHIP_TEXT_COLOR,
        ),
    )