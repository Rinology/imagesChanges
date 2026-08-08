import flet as ft

def main(page: ft.Page):
    def on_result(e: ft.FilePickerResultEvent):
        print(f"Result in event: {e.path}")
        page.window_close()
        
    def on_click(e):
        picker = ft.FilePicker(on_result=on_result)
        page.overlay.append(picker)
        page.update()
        print("Calling get_directory_path...")
        res = picker.get_directory_path()
        print(f"Result from function call: {res}")
        
    page.add(ft.ElevatedButton("Pick Folder", on_click=on_click))

ft.app(target=main)
