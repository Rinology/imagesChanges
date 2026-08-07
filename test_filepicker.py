import flet as ft

def main(page: ft.Page):
    picker = ft.FilePicker()
    
    # We purposefully do not add it to page.overlay
    # page.overlay.append(picker)

    def on_click(e):
        try:
            print("Calling get_directory_path...")
            picker.get_directory_path()
            print("Success!")
        except Exception as ex:
            print("Error:", ex)
            
    page.add(ft.ElevatedButton("Pick Folder", on_click=on_click))

ft.app(target=main)
