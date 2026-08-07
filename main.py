import flet as ft
from converter_app.flet_ui.main_window import MainWindow

def main(page: ft.Page):
    page.title = "이미지 변환 & 이름 변경 프로그램 v2 (WebP)"
    page.window.width = 1200
    page.window.height = 1000
    page.theme_mode = ft.ThemeMode.DARK
    
    main_window = MainWindow(page)
    
    def on_message(msg):
        if msg[0] == "progress":
            main_window.right_panel.update_progress(msg[1], msg[2])
            
    page.pubsub.subscribe(on_message)
    
    def toggle_theme(e):
        page.theme_mode = ft.ThemeMode.LIGHT if page.theme_mode == ft.ThemeMode.DARK else ft.ThemeMode.DARK
        page.update()
        
    page.appbar = ft.AppBar(
        title=ft.Text("이미지 변환 & 이름 변경 (WebP)"),
        actions=[
            ft.IconButton(ft.icons.BRIGHTNESS_4, on_click=toggle_theme, tooltip="테마 변경"),
            ft.Container(content=ft.Text("Made by rinology", size=12, color=ft.colors.ON_SURFACE_VARIANT), padding=10)
        ]
    )
    
    page.add(main_window)

if __name__ == "__main__":
    ft.app(target=main)
