import flet as ft
from converter_app.flet_ui.main_window import MainWindow

def main(page: ft.Page):
    page.title = "Image Converter"
    page.window_width = 1000
    page.window_height = 800
    
    main_window = MainWindow(page)
    page.add(main_window)

if __name__ == "__main__":
    ft.app(target=main)
