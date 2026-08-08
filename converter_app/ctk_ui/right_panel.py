import os
import customtkinter as ctk
from converter_app.core.image_processor import ImageProcessor
from converter_app.ctk_ui.rename_dialog import RenameDialog

class RightPanel(ctk.CTkFrame):
    def __init__(self, master, app_state, main_window):
        super().__init__(master)
        self.app_state = app_state
        self.main_window = main_window
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=3) # settings area
        self.grid_rowconfigure(1, weight=2) # log area
        
        self.build_ui()
        
    def build_ui(self):
        # 1. Settings (Top Right)
        settings_frame = ctk.CTkFrame(self)
        settings_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        settings_frame.grid_columnconfigure(0, weight=1)
        settings_frame.grid_rowconfigure(0, weight=1)
        
        self.tabview = ctk.CTkTabview(settings_frame, command=self.on_tab_change)
        self.tabview.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        self.tab_compress = self.tabview.add("압축 및 이름변경")
        self.tab_rename = self.tabview.add("단순 이름변경")
        
        self.build_compress_tab()
        self.build_rename_tab()
        
        self.btn_run = ctk.CTkButton(
            settings_frame, text="🚀 변환 실행", 
            font=ctk.CTkFont(size=15, weight="bold"),
            height=40,
            command=self.start_conversion
        )
        self.btn_run.grid(row=1, column=0, padx=10, pady=(0, 10))
        
        # 2. Log & Progress (Bottom Right)
        log_frame = ctk.CTkFrame(self)
        log_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(2, weight=1)
        
        ctk.CTkLabel(log_frame, text="진행 상태 및 로그", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, pady=(10, 0), padx=10, sticky="w")
        
        self.progress_bar = ctk.CTkProgressBar(log_frame)
        self.progress_bar.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        self.progress_bar.set(0)
        
        self.lbl_progress = ctk.CTkLabel(log_frame, text="대기 중...")
        self.lbl_progress.grid(row=1, column=0, pady=5)
        
        self.log_textbox = ctk.CTkTextbox(log_frame, state="disabled")
        self.log_textbox.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")
        
        credits = ctk.CTkLabel(log_frame, text="Developed by Taerin | GitHub", text_color="blue", cursor="hand2")
        credits.grid(row=3, column=0, padx=10, pady=(0, 5), sticky="e")
        
    def on_tab_change(self):
        self.main_window.on_settings_change()
        
    def build_compress_tab(self):
        parent = self.tab_compress
        parent.grid_columnconfigure(1, weight=1)
        
        # Row 0: Name input & separator
        ctk.CTkLabel(parent, text="변경할 이름:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.c_name_input = ctk.CTkEntry(parent, width=150)
        self.c_name_input.insert(0, "my image")
        self.c_name_input.grid(row=0, column=1, padx=5, pady=5, sticky="we")
        self.c_name_input.bind("<KeyRelease>", self.update_c_preview)
        
        self.c_sep_var = ctk.StringVar(value="_")
        sep_frame = ctk.CTkFrame(parent, fg_color="transparent")
        sep_frame.grid(row=0, column=2, padx=5, pady=5, sticky="w")
        ctk.CTkRadioButton(sep_frame, text="_ (언더바)", variable=self.c_sep_var, value="_", command=self.update_c_preview).pack(side="left", padx=5)
        ctk.CTkRadioButton(sep_frame, text="- (하이픈)", variable=self.c_sep_var, value="-", command=self.update_c_preview).pack(side="left", padx=5)
        
        ctk.CTkLabel(parent, text="(띄어쓰기는 연결 기호로 변환됨)", text_color="gray", font=ctk.CTkFont(size=11)).grid(row=0, column=3, padx=5, pady=5, sticky="w")
        
        # Row 1: Preview
        ctk.CTkLabel(parent, text="적용 예시:", text_color="blue").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.c_preview_lbl = ctk.CTkLabel(parent, text="", text_color="blue", font=ctk.CTkFont(weight="bold"))
        self.c_preview_lbl.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky="w")
        
        # Row 2: Save Location
        ctk.CTkLabel(parent, text="저장 위치:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.c_save_loc_var = ctk.StringVar(value="sub")
        loc_frame = ctk.CTkFrame(parent, fg_color="transparent")
        loc_frame.grid(row=2, column=1, columnspan=2, padx=5, pady=5, sticky="w")
        ctk.CTkRadioButton(loc_frame, text="현재 폴더", variable=self.c_save_loc_var, value="same", command=self.toggle_c_subfolder).pack(side="left", padx=5)
        ctk.CTkRadioButton(loc_frame, text="하위 폴더", variable=self.c_save_loc_var, value="sub", command=self.toggle_c_subfolder).pack(side="left", padx=10)
        
        # Row 3: Subfolder settings (conditionally shown)
        self.c_sub_row = ctk.CTkFrame(parent, fg_color="transparent")
        self.c_sub_row.grid(row=3, column=1, columnspan=2, padx=5, pady=5, sticky="w")
        ctk.CTkLabel(self.c_sub_row, text="└─ 폴더명:").pack(side="left", padx=(5, 5))
        self.c_sub_name = ctk.CTkEntry(self.c_sub_row, width=120)
        self.c_sub_name.insert(0, "output")
        self.c_sub_name.pack(side="left", padx=5)
        self.c_date_prefix = ctk.CTkOptionMenu(self.c_sub_row, values=["datetime", "date", "none"], width=100)
        self.c_date_prefix.set("datetime")
        self.c_date_prefix.pack(side="left", padx=5)
        ctk.CTkLabel(self.c_sub_row, text="(datetime: 20260808_123000, date: 20260808)", text_color="gray", font=ctk.CTkFont(size=11)).pack(side="left", padx=5)
        
        # Row 4: Original File
        ctk.CTkLabel(parent, text="원본 파일:").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.c_orig_var = ctk.StringVar(value="keep")
        orig_frame = ctk.CTkFrame(parent, fg_color="transparent")
        orig_frame.grid(row=4, column=1, columnspan=2, padx=5, pady=5, sticky="w")
        ctk.CTkRadioButton(orig_frame, text="유지 (복사)", variable=self.c_orig_var, value="keep").pack(side="left", padx=5)
        ctk.CTkRadioButton(orig_frame, text="삭제 (이동)", variable=self.c_orig_var, value="delete").pack(side="left", padx=10)
        
        # Row 5: Compression settings
        ctk.CTkLabel(parent, text="압축 설정:").grid(row=5, column=0, padx=5, pady=5, sticky="w")
        comp_frame = ctk.CTkFrame(parent, fg_color="transparent")
        comp_frame.grid(row=5, column=1, columnspan=2, padx=5, pady=5, sticky="w")
        ctk.CTkLabel(comp_frame, text="압축 강도:").pack(side="left")
        self.c_comp = ctk.CTkOptionMenu(comp_frame, values=["6", "4", "0"], width=80, command=lambda e: self.main_window.on_settings_change())
        self.c_comp.set("6")
        self.c_comp.pack(side="left", padx=5)
        ctk.CTkLabel(comp_frame, text="(0~6 지정, 6이 최고 압축률)", text_color="gray", font=ctk.CTkFont(size=11)).pack(side="left", padx=2)
        self.c_preview_size_var = ctk.BooleanVar(value=False)
        self.c_preview_size = ctk.CTkSwitch(comp_frame, text="예상 용량 계산 (느려짐)", variable=self.c_preview_size_var, command=lambda: self.main_window.on_settings_change())
        self.c_preview_size.pack(side="left", padx=15)
        
        self.update_c_preview()
        
    def toggle_c_subfolder(self):
        if self.c_save_loc_var.get() == "sub":
            self.c_sub_row.grid()
        else:
            self.c_sub_row.grid_remove()
            
    def update_c_preview(self, event=None):
        raw_name = self.c_name_input.get().strip()
        sep = self.c_sep_var.get()
        processed = raw_name.replace(" ", sep) if raw_name else "이름없음"
        self.c_preview_lbl.configure(text=f"{processed}{sep}1.webp")
        self.main_window.on_settings_change()
        
    def build_rename_tab(self):
        parent = self.tab_rename
        parent.grid_columnconfigure(1, weight=1)
        
        # Row 0: Name input & separator
        ctk.CTkLabel(parent, text="변경할 이름:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.r_name_input = ctk.CTkEntry(parent, width=150)
        self.r_name_input.insert(0, "사진 고양이")
        self.r_name_input.grid(row=0, column=1, padx=5, pady=5, sticky="we")
        self.r_name_input.bind("<KeyRelease>", self.update_r_preview)
        
        self.r_sep_var = ctk.StringVar(value="-")
        sep_frame = ctk.CTkFrame(parent, fg_color="transparent")
        sep_frame.grid(row=0, column=2, padx=5, pady=5, sticky="w")
        ctk.CTkRadioButton(sep_frame, text="_ (언더바)", variable=self.r_sep_var, value="_", command=self.update_r_preview).pack(side="left", padx=5)
        ctk.CTkRadioButton(sep_frame, text="- (하이픈)", variable=self.r_sep_var, value="-", command=self.update_r_preview).pack(side="left", padx=5)
        
        ctk.CTkLabel(parent, text="(띄어쓰기는 연결 기호로 변환됨)", text_color="gray", font=ctk.CTkFont(size=11)).grid(row=0, column=3, padx=5, pady=5, sticky="w")
        
        # Row 1: Pad & Ext
        pad_ext_frame = ctk.CTkFrame(parent, fg_color="transparent")
        pad_ext_frame.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky="w")
        
        ctk.CTkLabel(pad_ext_frame, text="숫자 패딩:").pack(side="left")
        self.r_pad = ctk.CTkOptionMenu(pad_ext_frame, values=["지정안함", "자동", "2자리", "3자리", "4자리", "5자리", "6자리"], width=100, command=self.update_r_preview)
        self.r_pad.set("자동")
        self.r_pad.pack(side="left", padx=5)
        ctk.CTkLabel(pad_ext_frame, text="(예: 3자리 선택 시 001, 002...)", text_color="gray", font=ctk.CTkFont(size=11)).pack(side="left", padx=2)
        
        ctk.CTkLabel(pad_ext_frame, text="확장자:").pack(side="left", padx=(15, 5))
        self.r_ext = ctk.CTkOptionMenu(pad_ext_frame, values=["원본 유지", ".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"], width=100, command=self.update_r_preview)
        self.r_ext.set("원본 유지")
        self.r_ext.pack(side="left", padx=5)
        ctk.CTkLabel(pad_ext_frame, text="(원본의 확장자가 강제 변경됩니다)", text_color="gray", font=ctk.CTkFont(size=11)).pack(side="left", padx=2)
        
        # Row 2: Preview
        ctk.CTkLabel(parent, text="적용 예시:", text_color="blue").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.r_preview_lbl = ctk.CTkLabel(parent, text="", text_color="blue", font=ctk.CTkFont(weight="bold"))
        self.r_preview_lbl.grid(row=2, column=1, columnspan=2, padx=5, pady=5, sticky="w")
        
        # Row 3: Save Location
        ctk.CTkLabel(parent, text="저장 위치:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.r_save_loc_var = ctk.StringVar(value="sub")
        loc_frame = ctk.CTkFrame(parent, fg_color="transparent")
        loc_frame.grid(row=3, column=1, columnspan=2, padx=5, pady=5, sticky="w")
        ctk.CTkRadioButton(loc_frame, text="현재 폴더", variable=self.r_save_loc_var, value="same", command=self.toggle_r_subfolder).pack(side="left", padx=5)
        ctk.CTkRadioButton(loc_frame, text="하위 폴더", variable=self.r_save_loc_var, value="sub", command=self.toggle_r_subfolder).pack(side="left", padx=10)
        
        # Row 4: Subfolder settings (conditionally shown)
        self.r_sub_row = ctk.CTkFrame(parent, fg_color="transparent")
        self.r_sub_row.grid(row=4, column=1, columnspan=2, padx=5, pady=5, sticky="w")
        ctk.CTkLabel(self.r_sub_row, text="└─ 폴더명:").pack(side="left", padx=(5, 5))
        self.r_sub_name = ctk.CTkEntry(self.r_sub_row, width=120)
        self.r_sub_name.insert(0, "renamed")
        self.r_sub_name.pack(side="left", padx=5)
        self.r_date_prefix = ctk.CTkOptionMenu(self.r_sub_row, values=["datetime", "date", "none"], width=100)
        self.r_date_prefix.set("none")
        self.r_date_prefix.pack(side="left", padx=5)
        ctk.CTkLabel(self.r_sub_row, text="(선택 시 날짜가 폴더명 앞에 붙습니다)", text_color="gray", font=ctk.CTkFont(size=11)).pack(side="left", padx=5)
        
        # Row 5: Original File
        ctk.CTkLabel(parent, text="원본 파일:").grid(row=5, column=0, padx=5, pady=5, sticky="w")
        self.r_orig_var = ctk.StringVar(value="keep")
        orig_frame = ctk.CTkFrame(parent, fg_color="transparent")
        orig_frame.grid(row=5, column=1, columnspan=2, padx=5, pady=5, sticky="w")
        ctk.CTkRadioButton(orig_frame, text="유지 (복사)", variable=self.r_orig_var, value="keep").pack(side="left", padx=5)
        ctk.CTkRadioButton(orig_frame, text="삭제 (이동)", variable=self.r_orig_var, value="delete").pack(side="left", padx=10)
        
        self.update_r_preview()
        
    def toggle_r_subfolder(self):
        if self.r_save_loc_var.get() == "sub":
            self.r_sub_row.grid()
        else:
            self.r_sub_row.grid_remove()
            
    def update_r_preview(self, event=None):
        raw_name = self.r_name_input.get().strip()
        sep = self.r_sep_var.get()
        processed = raw_name.replace(" ", sep) if raw_name else "이름없음"
        
        pad_val = self.r_pad.get()
        if pad_val == "지정안함": pad = "1"
        elif pad_val in ["자동", "2자리"]: pad = "01"
        elif pad_val == "3자리": pad = "001"
        elif pad_val == "4자리": pad = "0001"
        elif pad_val == "5자리": pad = "00001"
        elif pad_val == "6자리": pad = "000001"
        else: pad = "1"
        
        ext = ".확장자" if self.r_ext.get() == "원본 유지" else self.r_ext.get()
        self.r_preview_lbl.configure(text=f"{processed}{sep}{pad}{ext}")
        self.main_window.on_settings_change()
        
    def get_current_mode(self):
        return "compress" if self.tabview.get() == "압축 및 이름변경" else "rename"
        
    def get_compression_settings(self):
        return {
            'mode': 'compress',
            'raw_name': self.c_name_input.get().strip(),
            'separator': self.c_sep_var.get(),
            'save_location': self.c_save_loc_var.get(),
            'subfolder_name': self.c_sub_name.get().strip(),
            'date_prefix': self.c_date_prefix.get(),
            'delete_orig': self.c_orig_var.get() == "delete",
            'compression_method': self.c_comp.get(),
            'preview_size_val': self.c_preview_size_var.get()
        }

    def get_rename_settings(self):
        return {
            'mode': 'rename',
            'raw_name': self.r_name_input.get().strip(),
            'separator': self.r_sep_var.get(),
            'save_location': self.r_save_loc_var.get(),
            'subfolder_name': self.r_sub_name.get().strip(),
            'date_prefix': self.r_date_prefix.get(),
            'delete_orig': self.r_orig_var.get() == "delete",
            'pad_mode': self.r_pad.get(),
            'target_ext': self.r_ext.get()
        }
        
    def log(self, message):
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", message + "\n")
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")

    def update_progress(self, current, total):
        progress = (current / total) if total > 0 else 0
        self.progress_bar.set(progress)
        
        self.lbl_progress.configure(text=f"진행 상태: {current} / {total} 완료")
        if current == total and total > 0:
            self.lbl_progress.configure(text="완료!")
            
    def set_run_state(self, is_running):
        state = "disabled" if is_running else "normal"
        self.btn_run.configure(state=state)
        # Assuming you disable tabs as well during run, but left out for simplicity
        
    def start_conversion(self):
        if not self.app_state.get('selected_folder'):
            self.log("❌ 먼저 폴더를 선택해주세요.")
            return
            
        selected_files = self.main_window.get_selected_files()
        if not selected_files:
            self.log("❌ 처리할 이미지를 선택해주세요.")
            return
            
        mode = self.get_current_mode()
        
        if mode == 'compress':
            settings = self.get_compression_settings()
            if not settings['raw_name']:
                self.log("❌ 변경할 이름을 입력해주세요.")
                return
            self.execute_run(selected_files, settings)
        else:
            settings = self.get_rename_settings()
            if not settings['raw_name']:
                self.log("❌ 변경할 이름을 입력해주세요.")
                return
                
            base_name = settings['raw_name'].replace(" ", settings['separator'])
            total_files = len(selected_files)
            
            pad_val = settings['pad_mode']
            if pad_val == "지정안함": pad_length = 1
            elif pad_val == "자동": pad_length = len(str(total_files))
            elif pad_val == "2자리": pad_length = 2
            elif pad_val == "3자리": pad_length = 3
            elif pad_val == "4자리": pad_length = 4
            elif pad_val == "5자리": pad_length = 5
            elif pad_val == "6자리": pad_length = 6
            else: pad_length = 1
            
            new_names = []
            for i, filename in enumerate(selected_files):
                idx_str = str(i + 1).zfill(pad_length)
                ext = os.path.splitext(filename)[1] if settings['target_ext'] == "원본 유지" else settings['target_ext']
                new_names.append(f"{base_name}{settings['separator']}{idx_str}{ext}")
                
            def on_confirm():
                self.execute_run(selected_files, settings)
                
            RenameDialog(self.winfo_toplevel(), selected_files, new_names, on_confirm)
            
    def execute_run(self, selected_files, settings):
        self.main_window.set_run_state(True)
        self.progress_bar.set(0)
        self.lbl_progress.configure(text="진행 중...")
        
        # For thread safety, we use after() in callbacks to update UI
        def log_cb(msg):
            self.after(0, lambda: self.log(msg))
            
        def progress_cb(current, total):
            self.after(0, lambda: self.update_progress(current, total))
            
        def done_cb(success, errors, bytes_saved):
            self.after(0, lambda: self.main_window.set_run_state(False))
            
        callbacks = {
            'log': log_cb,
            'progress': progress_cb,
            'done': done_cb
        }
        
        if settings.get('mode') == 'rename':
            ImageProcessor.rename_images_async(
                selected_files, self.app_state['selected_folder'], settings['raw_name'], settings['separator'],
                settings['save_location'], settings['subfolder_name'], settings['date_prefix'], settings['delete_orig'],
                callbacks, settings['pad_mode'], settings['target_ext']
            )
        else:
            ImageProcessor.process_images_async(
                selected_files, self.app_state['selected_folder'], settings['raw_name'], settings['separator'],
                settings['save_location'], settings['subfolder_name'], settings['date_prefix'], settings['delete_orig'],
                settings['compression_method'], self.app_state['rotations'], callbacks
            )
