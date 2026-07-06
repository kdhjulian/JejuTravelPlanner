import flet as ft


def main(page: ft.Page) -> None:
    page.title = "제주 여행 플래너"

    status_text = ft.Text(
        value="환경 설정이 정상적으로 완료되었습니다.",
        size=18,
    )

    def confirm_environment(event: ft.ControlEvent) -> None:
        status_text.value = "버튼 이벤트도 정상적으로 동작합니다."
        page.update()

    page.add(
        ft.Column(
            controls=[
                ft.Text(
                    value="🏝️ 제주 여행 플래너",
                    size=30,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Text(
                    value="Day 1 · Flet 실행 확인",
                    size=20,
                ),
                status_text,
                ft.FilledButton(
                    content="환경 확인",
                    on_click=confirm_environment,
                ),
            ],
            spacing=16,
        )
    )


ft.run(main)
