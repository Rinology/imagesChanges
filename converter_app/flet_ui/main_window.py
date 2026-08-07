import flet as ft
from converter_app.flet_ui.left_panel import LeftPanel
from converter_app.flet_ui.right_panel import RightPanel

class MainWindow(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__(expand=True)
        self.app_page = page
        
        self.app_state = {
            'selected_folder': "",
            'image_files': [],
            'rotations': {}
        }
        
        self.left_panel = LeftPanel(self.app_page, self.app_state, self)
        self.right_panel = RightPanel(self.app_page, self.app_state, self)
        
        self.content = ft.Row(
            controls=[
                ft.Container(content=self.left_panel, expand=True, padding=10),
                ft.VerticalDivider(width=1, color=ft.Colors.OUTLINE),
                ft.Container(content=self.right_panel, expand=True, padding=10)
            ],
            expand=True
        )
        
        self.app_page.pubsub.subscribe(self.on_pubsub_message)
        
    def on_pubsub_message(self, msg):
        if isinstance(msg, tuple) and len(msg) == 3 and msg[0] == "progress":
            _, current, total = msg
            self.right_panel.update_progress(current, total)
            
    def get_selected_files(self):
        return self.left_panel.get_selected_files()
        
    def get_compression_settings(self):
        return self.right_panel.get_compression_settings()
        
    def get_current_mode(self):
        return self.right_panel.get_current_mode()
        
    def on_selection_change(self):
        self.left_panel.update_preview()
        
    def on_settings_change(self):
        self.left_panel.update_preview()
        
    def set_run_state(self, is_running):
        self.left_panel.disabled = is_running
        self.right_panel.set_run_state(is_running)
        self.app_page.update()
        
    def log(self, message):
        self.right_panel.log(message)
