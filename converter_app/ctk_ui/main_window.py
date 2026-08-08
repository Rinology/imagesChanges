import customtkinter as ctk
from converter_app.ctk_ui.left_panel import LeftPanel
from converter_app.ctk_ui.right_panel import RightPanel

class MainWindow(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        
        self.app_state = {
            'selected_folder': "",
            'image_files': [],
            'rotations': {}
        }
        
        self.grid_columnconfigure(0, weight=1, uniform="group1")
        self.grid_columnconfigure(1, weight=1, uniform="group1")
        self.grid_rowconfigure(0, weight=1)
        
        self.left_panel = LeftPanel(self, app_state=self.app_state, main_window=self)
        self.left_panel.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        self.right_panel = RightPanel(self, app_state=self.app_state, main_window=self)
        self.right_panel.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
    def get_selected_files(self):
        return self.left_panel.get_selected_files()
        
    def get_compression_settings(self):
        return self.right_panel.get_compression_settings()
        
    def get_current_mode(self):
        return self.right_panel.get_current_mode()
        
    def on_selection_change(self):
        self.left_panel.update_preview()
        
    def on_settings_change(self, *args):
        self.left_panel.refresh_listbox()
        self.left_panel.update_preview()
        
    def set_run_state(self, is_running):
        self.left_panel.set_run_state(is_running)
        self.right_panel.set_run_state(is_running)
        
    def log(self, message):
        self.right_panel.log(message)
