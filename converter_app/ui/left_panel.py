import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

class LeftPanel(ttk.Frame):
    def __init__(self, master, app_state, callbacks, **kwargs):
        super().__init__(master, **kwargs)
        self.app_state = app_state
        self.callbacks = callbacks # dict containing 'on_selection_change', 'on_run', 'on_folder_select', 'on_log'
        
        # State variables tied to UI
        self.entry_basename_var = tk.StringVar(value="my image")
        self.separator_var = tk.StringVar(value="_")
        self.save_loc_var = tk.StringVar(value="sub")
        self.subfolder_name_var = tk.StringVar(value="output")
        self.date_prefix_var = tk.StringVar(value="datetime")
        self.original_var = tk.StringVar(value="keep")
        self.compression_var = tk.StringVar(value="6")
        self.preview_size_var = tk.BooleanVar(value=False)
        
        self.setup_ui()
        
    def setup_ui(self):
        # 1. Folder Selection
        folder_frame = ttk.LabelFrame(self, text="1. 폴더 선택", padding=10)
        folder_frame.pack(fill=tk.X, pady=(0, 5))
        
        btn_select_folder = ttk.Button(folder_frame, text="폴더 열기", command=self.select_folder)
        btn_select_folder.pack(side=tk.LEFT, padx=(0, 10))
        
        self.lbl_folder_path = ttk.Label(folder_frame, text="선택된 폴더 없음", foreground="gray")
        self.lbl_folder_path.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 2. File List
        list_frame = ttk.LabelFrame(self, text="2. 이미지 파일 목록 (순서 변경 및 선택)", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.lbl_file_count = ttk.Label(list_frame, text="선택된 파일: 0 / 0개")
        self.lbl_file_count.pack(anchor=tk.W, pady=(0, 5))
        
        list_content_frame = ttk.Frame(list_frame)
        list_content_frame.pack(fill=tk.BOTH, expand=True)
        
        scroll_frame = ttk.Frame(list_content_frame)
        scroll_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.scrollbar = ttk.Scrollbar(scroll_frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.listbox = tk.Listbox(scroll_frame, selectmode=tk.EXTENDED, yscrollcommand=self.scrollbar.set, font=("Consolas", 10), exportselection=False)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.config(command=self.listbox.yview)
        self.listbox.bind("<<ListboxSelect>>", self.on_listbox_select)
        
        btn_frame = ttk.Frame(list_content_frame)
        btn_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        ttk.Button(btn_frame, text="전체 선택", command=self.select_all).pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="선택 해제", command=self.deselect_all).pack(fill=tk.X, pady=2)
        ttk.Label(btn_frame, text="").pack(pady=5)
        ttk.Button(btn_frame, text="▲ 위로 이동", command=self.move_up).pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="▼ 아래로 이동", command=self.move_down).pack(fill=tk.X, pady=2)
        ttk.Label(btn_frame, text="").pack(pady=5)
        ttk.Button(btn_frame, text="❌ 선택 항목 제외", command=self.remove_from_list).pack(fill=tk.X, pady=2)

        # 3. Settings
        settings_frame = ttk.LabelFrame(self, text="3. 변환 설정", padding=10)
        settings_frame.pack(fill=tk.X, pady=5)
        
        # Name
        name_frame = ttk.Frame(settings_frame)
        name_frame.pack(fill=tk.X, pady=2)
        ttk.Label(name_frame, text="변경할 이름 (영문):").pack(side=tk.LEFT)
        self.entry_basename = ttk.Entry(name_frame, textvariable=self.entry_basename_var, width=20)
        self.entry_basename.pack(side=tk.LEFT, padx=10)
        self.entry_basename_var.trace_add("write", self.update_name_preview)
        
        # Separator
        sep_frame = ttk.Frame(settings_frame)
        sep_frame.pack(fill=tk.X, pady=2)
        ttk.Label(sep_frame, text="이름 연결 기호:").pack(side=tk.LEFT)
        ttk.Radiobutton(sep_frame, text="_ (언더바)", variable=self.separator_var, value="_", command=self.update_name_preview).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(sep_frame, text="- (하이픈)", variable=self.separator_var, value="-", command=self.update_name_preview).pack(side=tk.LEFT, padx=5)
        
        hint_label = ttk.Label(settings_frame, text="* 띄어쓰기 입력 시 위의 이름 연결 기호로 대체됩니다.", foreground="gray", font=("Consolas", 8))
        hint_label.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # Name Preview
        preview_frame = ttk.Frame(settings_frame)
        preview_frame.pack(fill=tk.X, pady=2)
        ttk.Label(preview_frame, text="적용 예시:", foreground="blue").pack(side=tk.LEFT)
        self.lbl_name_preview = ttk.Label(preview_frame, text="", font=("Consolas", 10, "bold"), foreground="blue")
        self.lbl_name_preview.pack(side=tk.LEFT, padx=10)
        self.update_name_preview()
        
        # Save Location
        self.loc_frame = ttk.Frame(settings_frame)
        self.loc_frame.pack(fill=tk.X, pady=5)
        ttk.Label(self.loc_frame, text="저장 위치:").pack(side=tk.LEFT)
        ttk.Radiobutton(self.loc_frame, text="현재 폴더", variable=self.save_loc_var, value="same", command=self.toggle_subfolder_options).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(self.loc_frame, text="하위 폴더", variable=self.save_loc_var, value="sub", command=self.toggle_subfolder_options).pack(side=tk.LEFT, padx=5)
        
        self.subfolder_frame = ttk.Frame(settings_frame)
        self.subfolder_frame.pack(fill=tk.X, pady=2)
        ttk.Label(self.subfolder_frame, text="폴더명:").pack(side=tk.LEFT)
        ttk.Entry(self.subfolder_frame, textvariable=self.subfolder_name_var, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(self.subfolder_frame, text="년월일시", variable=self.date_prefix_var, value="datetime").pack(side=tk.LEFT)
        ttk.Radiobutton(self.subfolder_frame, text="년월일", variable=self.date_prefix_var, value="date").pack(side=tk.LEFT)
        ttk.Radiobutton(self.subfolder_frame, text="사용안함", variable=self.date_prefix_var, value="none").pack(side=tk.LEFT)

        # Keep original
        orig_frame = ttk.Frame(settings_frame)
        orig_frame.pack(fill=tk.X, pady=5)
        ttk.Label(orig_frame, text="원본 파일:").pack(side=tk.LEFT)
        ttk.Radiobutton(orig_frame, text="유지", variable=self.original_var, value="keep").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(orig_frame, text="삭제", variable=self.original_var, value="delete").pack(side=tk.LEFT, padx=5)

        # Compression
        comp_frame = ttk.Frame(settings_frame)
        comp_frame.pack(fill=tk.X, pady=5)
        ttk.Label(comp_frame, text="압축 강도:").pack(side=tk.LEFT)
        ttk.Radiobutton(comp_frame, text="최대(느림/최소)", variable=self.compression_var, value="6", command=self.trigger_size_update).pack(side=tk.LEFT, padx=2)
        ttk.Radiobutton(comp_frame, text="일반(적정)", variable=self.compression_var, value="4", command=self.trigger_size_update).pack(side=tk.LEFT, padx=2)
        ttk.Radiobutton(comp_frame, text="빠름(용량증가)", variable=self.compression_var, value="0", command=self.trigger_size_update).pack(side=tk.LEFT, padx=2)
        ttk.Checkbutton(comp_frame, text="예상 용량 계산 (느려짐)", variable=self.preview_size_var, command=self.trigger_size_update).pack(side=tk.LEFT, padx=10)

        # 4. Run Button
        run_frame = ttk.Frame(self)
        run_frame.pack(fill=tk.X, pady=10)
        self.btn_run = ttk.Button(run_frame, text="🚀 변환 실행", command=self.start_conversion)
        self.btn_run.pack(fill=tk.X, ipady=10)

    def select_folder(self):
        folder = filedialog.askdirectory(title="이미지가 있는 폴더를 선택하세요")
        if folder:
            self.app_state['selected_folder'] = folder
            self.lbl_folder_path.config(text=folder, foreground="black")
            if 'on_folder_select' in self.callbacks:
                self.callbacks['on_folder_select'](folder)

    def load_images_to_list(self, files):
        self.listbox.delete(0, tk.END)
        for f in files:
            self.listbox.insert(tk.END, f)
        self.select_all()

    def update_name_preview(self, *args):
        raw_name = self.entry_basename_var.get().strip()
        sep = self.separator_var.get()
        processed_name = raw_name.replace(" ", sep)
        if not processed_name:
            processed_name = "이름없음"
        self.lbl_name_preview.config(text=f"{processed_name}{sep}1.webp")

    def toggle_subfolder_options(self):
        if self.save_loc_var.get() == "sub":
            self.subfolder_frame.pack(fill=tk.X, pady=2, after=self.loc_frame)
        else:
            self.subfolder_frame.pack_forget()

    def update_file_count_label(self):
        total = self.listbox.size()
        selected = len(self.listbox.curselection())
        self.lbl_file_count.config(text=f"선택된 파일: {selected} / {total}개")

    def select_all(self):
        self.listbox.select_set(0, tk.END)
        self.on_listbox_select()

    def deselect_all(self):
        self.listbox.selection_clear(0, tk.END)
        self.on_listbox_select()

    def move_up(self):
        pos_list = self.listbox.curselection()
        if not pos_list: return
        for pos in pos_list:
            if pos == 0: continue
            item = self.listbox.get(pos)
            self.listbox.delete(pos)
            self.listbox.insert(pos - 1, item)
            self.listbox.select_set(pos - 1)
        self.on_listbox_select()

    def move_down(self):
        pos_list = self.listbox.curselection()
        if not pos_list: return
        for pos in reversed(pos_list):
            if pos == self.listbox.size() - 1: continue
            item = self.listbox.get(pos)
            self.listbox.delete(pos)
            self.listbox.insert(pos + 1, item)
            self.listbox.select_set(pos + 1)
        self.on_listbox_select()

    def remove_from_list(self):
        selected_indices = self.listbox.curselection()
        if not selected_indices: return
        
        removed_count = 0
        for pos in reversed(selected_indices):
            filename = self.listbox.get(pos)
            self.listbox.delete(pos)
            if filename in self.app_state['image_files']:
                self.app_state['image_files'].remove(filename)
                removed_count += 1
                
        self.on_listbox_select()
        if removed_count > 0 and 'on_log' in self.callbacks:
            self.callbacks['on_log'](f"🗑️ 목록에서 {removed_count}개의 파일이 제외되었습니다.")

    def on_listbox_select(self, event=None):
        self.update_file_count_label()
        
        for i in range(self.listbox.size()):
            self.listbox.itemconfig(i, background="white", foreground="black")
            
        selected_indices = self.listbox.curselection()
        for i in selected_indices:
            self.listbox.itemconfig(i, background="#0078D7", foreground="white")
            
        if 'on_selection_change' in self.callbacks:
            self.callbacks['on_selection_change']([self.listbox.get(i) for i in selected_indices])

    def trigger_size_update(self):
        if 'on_selection_change' in self.callbacks:
            selected_indices = self.listbox.curselection()
            self.callbacks['on_selection_change']([self.listbox.get(i) for i in selected_indices])

    def start_conversion(self):
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
            self.callbacks['on_run']([self.listbox.get(i) for i in selected_indices], settings)

    def set_run_button_state(self, state):
        self.btn_run.config(state=state)
