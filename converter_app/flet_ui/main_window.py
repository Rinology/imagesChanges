import flet as ft
from converter_app.flet_ui.left_panel import LeftPanel
from converter_app.flet_ui.right_panel import RightPanel

class MainWindow(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__(expand=True)
        self.page = page
        
        self.app_state = {
            'selected_folder': "",
            'image_files': [],
            'rotations': {}
        }
        self.content = self.build_ui()
        
    def build_ui(self):
        self.left_panel = LeftPanel(
            self.page, self.app_state, 
            on_selection_change=self.on_selection_change,
            on_log=self.on_log,
            on_update_preview=self.on_update_preview,
            on_run=self.on_run,
            on_file_rotated=self.on_file_rotated
        )
        self.right_panel = RightPanel(
            self.page, self.app_state,
            on_rotate_request=self.left_panel.handle_rotate
        )
        
        return ft.Row(
            controls=[
                ft.Container(content=self.left_panel, expand=True, padding=10),
                ft.VerticalDivider(width=1, color=ft.colors.OUTLINE),
                ft.Container(content=self.right_panel, expand=True, padding=10)
            ],
            expand=True
        )
        
    def on_selection_change(self, selected_files):
        self.right_panel.update_selection(selected_files, self.left_panel.preview_size_val, self.left_panel.compression_val)

    def on_log(self, message):
        self.right_panel.log(message)
        
    def on_update_preview(self, selected_files):
        self.right_panel.update_selection(selected_files, self.left_panel.preview_size_val, self.left_panel.compression_val)
        
    def on_run(self, started):
        if started:
            self.right_panel.reset_progress()
        else:
            self.left_panel.set_run_button_state(False)

    def on_file_rotated(self, filepath):
        self.right_panel.update_selection_after_rotate()
