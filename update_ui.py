import re
import os

filepath = 'converter_app/ui/left_panel.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Add imports for dialog
import_str = "from tkinter import ttk, filedialog, messagebox\nfrom converter_app.ui.rename_preview_dialog import RenamePreviewDialog\n"
content = content.replace("from tkinter import ttk, filedialog, messagebox\n", import_str)

# Drag and drop bindings
listbox_binds = """        self.scrollbar.config(command=self.listbox.yview)
        self.listbox.bind("<<ListboxSelect>>", self.on_listbox_select)
        
        # Drag and Drop bindings
        self.listbox.bind("<ButtonPress-1>", self.on_drag_start)
        self.listbox.bind("<B1-Motion>", self.on_drag_motion)
        self.listbox.bind("<ButtonRelease-1>", self.on_drag_end)"""
content = content.replace('        self.scrollbar.config(command=self.listbox.yview)\n        self.listbox.bind("<<ListboxSelect>>", self.on_listbox_select)', listbox_binds)

# Setup UI - Add Notebook at the top
setup_ui_start = """    def setup_ui(self):
        # 0. Mode Switcher (Notebook)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.X, pady=(0, 5))
        
        self.tab_compress = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_compress, text="압축 및 이름변경")
        
        self.tab_rename = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_rename, text="단순 이름변경")
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

        # 1. Folder Selection"""
content = content.replace('    def setup_ui(self):\n        # 1. Folder Selection', setup_ui_start)

# Rename Settings Frame
rename_settings_code = """
        # --- 3-2. Rename Settings ---
        self.rename_settings_frame = ttk.LabelFrame(self, text="3. 이름 변경 설정", padding=10)
        
        # Name
        r_name_frame = ttk.Frame(self.rename_settings_frame)
        r_name_frame.pack(fill=tk.X, pady=2)
        ttk.Label(r_name_frame, text="변경할 이름:").pack(side=tk.LEFT)
        self.entry_rename_basename_var = tk.StringVar(value="사진 고양이")
        self.entry_rename_basename = ttk.Entry(r_name_frame, textvariable=self.entry_rename_basename_var, width=20)
        self.entry_rename_basename.pack(side=tk.LEFT, padx=10)
        self.entry_rename_basename_var.trace_add("write", self.update_rename_preview)
        
        # Separator
        r_sep_frame = ttk.Frame(self.rename_settings_frame)
        r_sep_frame.pack(fill=tk.X, pady=2)
        ttk.Label(r_sep_frame, text="이름 연결 기호:").pack(side=tk.LEFT)
        self.rename_separator_var = tk.StringVar(value="-")
        ttk.Radiobutton(r_sep_frame, text="_ (언더바)", variable=self.rename_separator_var, value="_", command=self.update_rename_preview).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(r_sep_frame, text="- (하이픈)", variable=self.rename_separator_var, value="-", command=self.update_rename_preview).pack(side=tk.LEFT, padx=5)
        
        # Options
        r_opt_frame = ttk.Frame(self.rename_settings_frame)
        r_opt_frame.pack(fill=tk.X, pady=5)
        ttk.Label(r_opt_frame, text="숫자 패딩(01, 02):").pack(side=tk.LEFT)
        self.rename_zero_pad_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(r_opt_frame, text="사용", variable=self.rename_zero_pad_var, command=self.update_rename_preview).pack(side=tk.LEFT, padx=5)
        
        # Name Preview
        r_preview_frame = ttk.Frame(self.rename_settings_frame)
        r_preview_frame.pack(fill=tk.X, pady=2)
        ttk.Label(r_preview_frame, text="적용 예시:", foreground="blue").pack(side=tk.LEFT)
        self.lbl_rename_preview = ttk.Label(r_preview_frame, text="", font=("Consolas", 10, "bold"), foreground="blue")
        self.lbl_rename_preview.pack(side=tk.LEFT, padx=10)
        self.update_rename_preview()
        
        # Save Location
        self.r_loc_frame = ttk.Frame(self.rename_settings_frame)
        self.r_loc_frame.pack(fill=tk.X, pady=5)
        ttk.Label(self.r_loc_frame, text="저장 위치:").pack(side=tk.LEFT)
        self.rename_save_loc_var = tk.StringVar(value="sub")
        ttk.Radiobutton(self.r_loc_frame, text="현재 폴더", variable=self.rename_save_loc_var, value="same", command=self.toggle_rename_subfolder).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(self.r_loc_frame, text="하위 폴더", variable=self.rename_save_loc_var, value="sub", command=self.toggle_rename_subfolder).pack(side=tk.LEFT, padx=5)
        
        self.r_subfolder_frame = ttk.Frame(self.rename_settings_frame)
        self.r_subfolder_frame.pack(fill=tk.X, pady=2)
        ttk.Label(self.r_subfolder_frame, text="폴더명:").pack(side=tk.LEFT)
        self.rename_subfolder_name_var = tk.StringVar(value="renamed")
        ttk.Entry(self.r_subfolder_frame, textvariable=self.rename_subfolder_name_var, width=10).pack(side=tk.LEFT, padx=5)
        self.rename_date_prefix_var = tk.StringVar(value="none")
        ttk.Radiobutton(self.r_subfolder_frame, text="년월일시", variable=self.rename_date_prefix_var, value="datetime").pack(side=tk.LEFT)
        ttk.Radiobutton(self.r_subfolder_frame, text="년월일", variable=self.rename_date_prefix_var, value="date").pack(side=tk.LEFT)
        ttk.Radiobutton(self.r_subfolder_frame, text="사용안함", variable=self.rename_date_prefix_var, value="none").pack(side=tk.LEFT)
        
        # Keep original
        r_orig_frame = ttk.Frame(self.rename_settings_frame)
        r_orig_frame.pack(fill=tk.X, pady=5)
        ttk.Label(r_orig_frame, text="원본 파일:").pack(side=tk.LEFT)
        self.rename_original_var = tk.StringVar(value="keep")
        ttk.Radiobutton(r_orig_frame, text="유지 (복사)", variable=self.rename_original_var, value="keep").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(r_orig_frame, text="삭제 (이동)", variable=self.rename_original_var, value="delete").pack(side=tk.LEFT, padx=5)

        # 4. Run Button"""
content = content.replace("        # 4. Run Button", rename_settings_code)

content = content.replace("        settings_frame = ttk.LabelFrame(self, text=\"3. 변환 설정\", padding=10)", "        self.settings_frame = ttk.LabelFrame(self, text=\"3. 변환 설정\", padding=10)\n        self.active_settings = self.settings_frame")

content = content.replace("        run_frame = ttk.Frame(self)\n        run_frame.pack(fill=tk.X, pady=10)", "        self.run_frame = ttk.Frame(self)\n        self.run_frame.pack(fill=tk.X, pady=10)")
content = content.replace("        self.btn_run = ttk.Button(run_frame, text=\"🚀 변환 실행\", command=self.start_conversion)\n        self.btn_run.pack(fill=tk.X, ipady=10)", "        self.btn_run = ttk.Button(self.run_frame, text=\"🚀 변환 실행\", command=self.start_conversion)\n        self.btn_run.pack(fill=tk.X, ipady=10)")

# Add settings_frame property if missing.
content = content.replace("settings_frame.pack", "self.settings_frame.pack")
content = content.replace("name_frame = ttk.Frame(settings_frame)", "name_frame = ttk.Frame(self.settings_frame)")
content = content.replace("sep_frame = ttk.Frame(settings_frame)", "sep_frame = ttk.Frame(self.settings_frame)")
content = content.replace("hint_label = ttk.Label(settings_frame", "hint_label = ttk.Label(self.settings_frame")
content = content.replace("preview_frame = ttk.Frame(settings_frame)", "preview_frame = ttk.Frame(self.settings_frame)")
content = content.replace("self.loc_frame = ttk.Frame(settings_frame)", "self.loc_frame = ttk.Frame(self.settings_frame)")
content = content.replace("self.subfolder_frame = ttk.Frame(settings_frame)", "self.subfolder_frame = ttk.Frame(self.settings_frame)")
content = content.replace("orig_frame = ttk.Frame(settings_frame)", "orig_frame = ttk.Frame(self.settings_frame)")
content = content.replace("comp_frame = ttk.Frame(settings_frame)", "comp_frame = ttk.Frame(self.settings_frame)")

# Drag and drop logic and Notebook callbacks
extra_methods = """
    def on_tab_changed(self, event):
        tab_idx = self.notebook.index(self.notebook.select())
        if tab_idx == 0:
            self.rename_settings_frame.pack_forget()
            self.settings_frame.pack(fill=tk.X, pady=5, before=self.run_frame)
            self.btn_run.config(text="🚀 변환 실행")
        else:
            self.settings_frame.pack_forget()
            self.rename_settings_frame.pack(fill=tk.X, pady=5, before=self.run_frame)
            self.btn_run.config(text="📝 이름 변경 실행")

    def update_rename_preview(self, *args):
        raw_name = self.entry_rename_basename_var.get().strip()
        sep = self.rename_separator_var.get()
        processed_name = raw_name.replace(" ", sep)
        if not processed_name:
            processed_name = "이름없음"
        pad = "01" if self.rename_zero_pad_var.get() else "1"
        self.lbl_rename_preview.config(text=f"{processed_name}{sep}{pad}.확장자")

    def toggle_rename_subfolder(self):
        if self.rename_save_loc_var.get() == "sub":
            self.r_subfolder_frame.pack(fill=tk.X, pady=2, after=self.r_loc_frame)
        else:
            self.r_subfolder_frame.pack_forget()

    def on_drag_start(self, event):
        self.listbox._drag_start_index = self.listbox.nearest(event.y)
        
    def on_drag_motion(self, event):
        i = self.listbox.nearest(event.y)
        if i < 0 or getattr(self.listbox, '_drag_start_index', -1) < 0: return
        if i != self.listbox._drag_start_index:
            val = self.listbox.get(self.listbox._drag_start_index)
            self.listbox.delete(self.listbox._drag_start_index)
            self.listbox.insert(i, val)
            self.listbox.selection_clear(0, tk.END)
            self.listbox.select_set(i)
            self.listbox._drag_start_index = i

    def on_drag_end(self, event):
        self.on_listbox_select(event)
"""
content = content.replace("    def select_folder(self):", extra_methods + "\n    def select_folder(self):")


# Modification to start_conversion to support rename logic
start_conversion_original = """    def start_conversion(self):
        if not self.app_state.get('selected_folder'):
            messagebox.showwarning("경고", "먼저 폴더를 선택해주세요.")
            return
        
        selected_indices = self.listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("경고", "변환할 이미지를 선택해주세요.")
            return

        raw_name = self.entry_basename_var.get().strip()
        if not raw_name:
            messagebox.showwarning("경고", "변경할 영문 이름을 입력해주세요.")
            return
            
        settings = {
            'raw_name': raw_name,
            'separator': self.separator_var.get(),
            'save_location': self.save_loc_var.get(),
            'subfolder_name': self.subfolder_name_var.get().strip(),
            'date_prefix': self.date_prefix_var.get(),
            'delete_orig': self.original_var.get() == "delete",
            'compression_method': self.compression_var.get(),
            'preview_size': self.preview_size_var.get()
        }

        if 'on_run' in self.callbacks:
            self.callbacks['on_run']([self.listbox.get(i) for i in selected_indices], settings)"""

start_conversion_new = """    def start_conversion(self):
        if not self.app_state.get('selected_folder'):
            messagebox.showwarning("경고", "먼저 폴더를 선택해주세요.")
            return
        
        selected_indices = self.listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("경고", "처리할 이미지를 선택해주세요.")
            return

        selected_files = [self.listbox.get(i) for i in selected_indices]
        tab_idx = self.notebook.index(self.notebook.select())

        if tab_idx == 0:
            # 압축 및 이름변경
            raw_name = self.entry_basename_var.get().strip()
            if not raw_name:
                messagebox.showwarning("경고", "변경할 이름을 입력해주세요.")
                return
                
            settings = {
                'mode': 'compress',
                'raw_name': raw_name,
                'separator': self.separator_var.get(),
                'save_location': self.save_loc_var.get(),
                'subfolder_name': self.subfolder_name_var.get().strip(),
                'date_prefix': self.date_prefix_var.get(),
                'delete_orig': self.original_var.get() == "delete",
                'compression_method': self.compression_var.get(),
                'preview_size': self.preview_size_var.get()
            }
            if 'on_run' in self.callbacks:
                self.callbacks['on_run'](selected_files, settings)
        else:
            # 단순 이름변경
            raw_name = self.entry_rename_basename_var.get().strip()
            if not raw_name:
                messagebox.showwarning("경고", "변경할 이름을 입력해주세요.")
                return
                
            settings = {
                'mode': 'rename',
                'raw_name': raw_name,
                'separator': self.rename_separator_var.get(),
                'save_location': self.rename_save_loc_var.get(),
                'subfolder_name': self.rename_subfolder_name_var.get().strip(),
                'date_prefix': self.rename_date_prefix_var.get(),
                'delete_orig': self.rename_original_var.get() == "delete",
                'zero_padding': self.rename_zero_pad_var.get()
            }
            
            # 새 이름 목록 생성
            base_name = raw_name.replace(" ", settings['separator'])
            total_files = len(selected_files)
            pad_length = len(str(total_files)) if settings['zero_padding'] else 1
            
            new_names = []
            for i, filename in enumerate(selected_files):
                idx_str = str(i + 1).zfill(pad_length)
                ext = os.path.splitext(filename)[1]
                new_names.append(f"{base_name}{settings['separator']}{idx_str}{ext}")
                
            def on_confirm():
                if 'on_run' in self.callbacks:
                    self.callbacks['on_run'](selected_files, settings)
                    
            RenamePreviewDialog(self.winfo_toplevel(), selected_files, new_names, on_confirm)"""

content = content.replace(start_conversion_original, start_conversion_new)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated left_panel.py")
