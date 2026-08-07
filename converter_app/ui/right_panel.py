import tkinter as tk
from tkinter import ttk

class RightPanel(ttk.Frame):
    def __init__(self, master, app_state, callbacks, **kwargs):
        super().__init__(master, **kwargs)
        self.app_state = app_state
        self.callbacks = callbacks # dict containing 'on_rotate'
        self.preview_image_ref = None # 가비지 컬렉션 방지용
        
        self.setup_ui()
        
    def setup_ui(self):
        # 1. 썸네일 미리보기 영역
        preview_group = ttk.LabelFrame(self, text="이미지 미리보기", padding=10)
        preview_group.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        self.lbl_image_preview = ttk.Label(preview_group, text="리스트에서 이미지를 선택하면\n여기에 미리보기가 표시됩니다.", justify=tk.CENTER)
        self.lbl_image_preview.pack(fill=tk.BOTH, expand=True, pady=5)
        
        info_frame = ttk.Frame(preview_group)
        info_frame.pack(fill=tk.X, pady=5)
        
        self.lbl_image_info = ttk.Label(info_frame, text="")
        self.lbl_image_info.pack(side=tk.LEFT, padx=10, expand=True)
        
        self.btn_rotate = ttk.Button(info_frame, text="⟳ 90도 회전", command=self.rotate_current_image, state=tk.DISABLED)
        self.btn_rotate.pack(side=tk.RIGHT, padx=10)

        # 2. 진행 상태 및 로그 영역
        log_group = ttk.LabelFrame(self, text="진행 상태 및 로그", padding=10)
        log_group.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(log_group, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=(0, 5))
        
        self.lbl_progress_text = ttk.Label(log_group, text="대기 중...")
        self.lbl_progress_text.pack(anchor=tk.W, pady=(0, 5))
        
        log_scroll = ttk.Scrollbar(log_group)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.log_text = tk.Text(log_group, state=tk.DISABLED, font=("Consolas", 9), yscrollcommand=log_scroll.set)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        log_scroll.config(command=self.log_text.yview)

    def log(self, message):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def update_preview(self, photo, filename=""):
        if photo:
            self.lbl_image_preview.config(image=photo, text="")
            self.preview_image_ref = photo
            self.btn_rotate.config(state=tk.NORMAL)
            if filename:
                self.lbl_image_info.config(text=filename)
        else:
            self.lbl_image_preview.config(image='', text="선택된 이미지가 없거나 불러올 수 없습니다.")
            self.lbl_image_info.config(text=filename)
            self.btn_rotate.config(state=tk.DISABLED)
            self.preview_image_ref = None

    def update_info_text(self, text):
        self.lbl_image_info.config(text=text)

    def update_progress(self, current, total):
        progress = (current / total) * 100 if total > 0 else 0
        self.progress_var.set(progress)
        self.lbl_progress_text.config(text=f"진행 상태: {current} / {total} 완료")

    def reset_progress(self):
        self.progress_var.set(0)
        self.lbl_progress_text.config(text="대기 중...")

    def rotate_current_image(self):
        if 'on_rotate' in self.callbacks:
            self.callbacks['on_rotate']()
