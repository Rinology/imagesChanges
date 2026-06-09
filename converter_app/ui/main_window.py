import os
import tkinter as tk
from tkinter import ttk
import webbrowser

from converter_app.ui.left_panel import LeftPanel
from converter_app.ui.right_panel import RightPanel
from converter_app.core.image_processor import ImageProcessor

class ImageConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("이미지 변환 & 이름 변경 프로그램 v2 (WebP)")
        self.root.geometry("1200x1000")
        
        self.app_state = {
            'selected_folder': "",
            'image_files': [],
            'rotations': {}
        }
        
        self.setup_ui()

    def setup_ui(self):
        style = ttk.Style()
        style.configure("TButton", padding=5)
        
        self.setup_footer()
        
        self.paned_window = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        left_frame = ttk.Frame(self.paned_window)
        right_frame = ttk.Frame(self.paned_window)
        
        self.paned_window.add(left_frame, weight=1)
        self.paned_window.add(right_frame, weight=1)
        
        left_callbacks = {
            'on_folder_select': self.on_folder_select,
            'on_selection_change': self.on_selection_change,
            'on_run': self.on_run_conversion,
            'on_log': self.on_log
        }
        self.left_panel = LeftPanel(left_frame, self.app_state, left_callbacks)
        self.left_panel.pack(fill=tk.BOTH, expand=True)
        
        right_callbacks = {
            'on_rotate': self.on_rotate_current
        }
        self.right_panel = RightPanel(right_frame, self.app_state, right_callbacks)
        self.right_panel.pack(fill=tk.BOTH, expand=True)

    def setup_footer(self):
        footer_frame = ttk.Frame(self.root)
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=5)
        
        lbl_github = tk.Label(footer_frame, text="GitHub: https://github.com/rinology", fg="blue", cursor="hand2", font=("Consolas", 9, "underline"))
        lbl_github.pack(side=tk.LEFT)
        lbl_github.bind("<Button-1>", lambda e: webbrowser.open_new("https://github.com/rinology"))
        
        lbl_nickname = tk.Label(footer_frame, text="Made by rinology", fg="gray", font=("Consolas", 9))
        lbl_nickname.pack(side=tk.RIGHT)

    def on_folder_select(self, folder):
        self.app_state['image_files'] = []
        self.app_state['rotations'] = {}
        valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp')
        
        for f in os.listdir(folder):
            if f.lower().endswith(valid_extensions):
                self.app_state['image_files'].append(f)
                
        self.left_panel.load_images_to_list(self.app_state['image_files'])
        self.right_panel.log(f"📁 폴더에서 {len(self.app_state['image_files'])}개의 이미지를 불러왔습니다.")

    def on_selection_change(self, selected_files):
        if not selected_files:
            self.right_panel.update_preview(None, "")
            return
            
        first_file = selected_files[0]
        filepath = os.path.join(self.app_state['selected_folder'], first_file)
        
        try:
            rot = self.app_state['rotations'].get(filepath, 0)
            photo = ImageProcessor.create_thumbnail(filepath, rot)
            self.right_panel.update_preview(photo, "")
            
            # 용량 계산 로직
            orig_size = os.path.getsize(filepath)
            size_str = ImageProcessor.format_size(orig_size)
            
            if not self.left_panel.preview_size_var.get():
                self.right_panel.update_info_text(f"{first_file} ({size_str})")
            else:
                self.right_panel.update_info_text(f"{first_file} ({size_str}) -> 예상 변환 용량: 계산 중...")
                comp_method = self.left_panel.compression_var.get()
                
                def on_success(expected):
                    self.root.after(0, lambda: self.right_panel.update_info_text(
                        f"{first_file} ({size_str}) -> 예상 변환 용량: 약 {ImageProcessor.format_size(expected)}"
                    ))
                def on_error(err):
                    self.root.after(0, lambda: self.right_panel.update_info_text(
                        f"{first_file} ({size_str}) -> 예상 용량 계산 실패"
                    ))
                    
                ImageProcessor.calculate_expected_size_async(filepath, rot, comp_method, on_success, on_error)
                
        except Exception as e:
            self.right_panel.update_preview(None, first_file)

    def on_rotate_current(self):
        selected_indices = self.left_panel.listbox.curselection()
        if not selected_indices: return
        
        filename = self.left_panel.listbox.get(selected_indices[0])
        filepath = os.path.join(self.app_state['selected_folder'], filename)
        
        current_rot = self.app_state['rotations'].get(filepath, 0)
        self.app_state['rotations'][filepath] = (current_rot - 90) % 360
        
        self.left_panel.on_listbox_select()

    def on_log(self, message):
        self.right_panel.log(message)

    def on_run_conversion(self, selected_files, settings):
        self.left_panel.set_run_button_state(tk.DISABLED)
        self.right_panel.reset_progress()
        
        def log_cb(msg):
            self.root.after(0, lambda: self.right_panel.log(msg))
            
        def progress_cb(current, total):
            self.root.after(0, lambda: self.right_panel.update_progress(current, total))
            
        def done_cb(success_count, error_count, total_saved_bytes):
            self.root.after(0, lambda: self.left_panel.set_run_button_state(tk.NORMAL))
            
        callbacks = {
            'log': log_cb,
            'progress': progress_cb,
            'done': done_cb
        }
        
        ImageProcessor.process_images_async(
            selected_files,
            self.app_state['selected_folder'],
            settings['raw_name'],
            settings['separator'],
            settings['save_location'],
            settings['subfolder_name'],
            settings['date_prefix'],
            settings['delete_orig'],
            settings['compression_method'],
            self.app_state['rotations'],
            callbacks
        )
