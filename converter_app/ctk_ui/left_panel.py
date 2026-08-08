import os
import tkinter as tk
from tkinter import filedialog
from PIL import Image
import customtkinter as ctk
from converter_app.core.image_processor import ImageProcessor

class LeftPanel(ctk.CTkFrame):
    def __init__(self, master, app_state, main_window):
        super().__init__(master)
        self.app_state = app_state
        self.main_window = main_window
        self.current_preview_file = None
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self.build_ui()
        
    def build_ui(self):
        # 1. Folder Selection & File List
        folder_frame = ctk.CTkFrame(self)
        folder_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        folder_frame.grid_columnconfigure(1, weight=1)
        
        self.btn_open_folder = ctk.CTkButton(folder_frame, text="📂 폴더 열기", command=self.on_open_folder, width=100)
        self.btn_open_folder.grid(row=0, column=0, padx=(10, 5), pady=10)
        
        self.lbl_folder_path = ctk.CTkLabel(folder_frame, text="선택된 폴더 없음", text_color="gray")
        self.lbl_folder_path.grid(row=0, column=1, padx=5, pady=10, sticky="w")
        
        list_frame = ctk.CTkFrame(self)
        list_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(1, weight=1)
        
        ctk.CTkLabel(list_frame, text="이미지 파일 목록", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, columnspan=2, pady=(10, 0), sticky="w", padx=10)
        self.lbl_file_count = ctk.CTkLabel(list_frame, text="선택된 파일: 0 / 0개")
        self.lbl_file_count.grid(row=0, column=1, pady=(10, 0), sticky="e", padx=10)
        
        self.listbox = tk.Listbox(list_frame, selectmode=tk.EXTENDED, bg="#2b2b2b", fg="white", selectbackground="#1f538d", borderwidth=0, highlightthickness=0)
        self.listbox.grid(row=1, column=0, padx=(10, 5), pady=10, sticky="nsew")
        self.listbox.bind('<<ListboxSelect>>', lambda e: self.on_listbox_select())
        
        scrollbar = ctk.CTkScrollbar(list_frame, command=self.listbox.yview)
        scrollbar.grid(row=1, column=1, padx=(0, 5), pady=10, sticky="ns")
        self.listbox.configure(yscrollcommand=scrollbar.set)
        
        btn_frame = ctk.CTkFrame(list_frame, fg_color="transparent")
        btn_frame.grid(row=1, column=2, padx=5, pady=10, sticky="nw")
        
        ctk.CTkButton(btn_frame, text="전체 선택", command=self.select_all, width=100).pack(pady=2)
        ctk.CTkButton(btn_frame, text="선택 해제", command=self.deselect_all, width=100).pack(pady=2)
        ctk.CTkButton(btn_frame, text="▲ 위로 이동", command=self.move_up, width=100).pack(pady=(15, 2))
        ctk.CTkButton(btn_frame, text="▼ 아래로 이동", command=self.move_down, width=100).pack(pady=2)
        ctk.CTkButton(btn_frame, text="❌ 선택 제외", command=self.remove_from_list, width=100, fg_color="#c93434", hover_color="#a82b2b").pack(pady=(15, 2))
        
        # 2. Image Preview
        preview_frame = ctk.CTkFrame(self)
        preview_frame.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="ew")
        preview_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(preview_frame, text="이미지 미리보기", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, columnspan=2, pady=(10, 0), sticky="w", padx=10)
        
        self.lbl_image = ctk.CTkLabel(preview_frame, text="이미지 없음", text_color="gray", height=250)
        self.lbl_image.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        
        self.lbl_info = ctk.CTkLabel(preview_frame, text="선택된 이미지 없음")
        self.lbl_info.grid(row=2, column=0, padx=10, pady=10, sticky="w")
        
        self.btn_rotate = ctk.CTkButton(preview_frame, text="↻ 90도 회전", command=self.handle_rotate, width=100, state="disabled")
        self.btn_rotate.grid(row=2, column=1, padx=10, pady=10, sticky="e")
        
    def on_open_folder(self):
        path = filedialog.askdirectory(title="이미지가 있는 폴더를 선택하세요")
        if path:
            self.on_folder_selected(path)
            
    def on_folder_selected(self, path):
        self.app_state['selected_folder'] = path
        self.lbl_folder_path.configure(text=path, text_color=("black", "white"))
        
        self.app_state['image_files'] = []
        self.app_state['rotations'] = {}
        valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp')
        
        try:
            for f in os.listdir(path):
                if f.lower().endswith(valid_extensions):
                    self.app_state['image_files'].append(f)
        except Exception:
            pass
            
        self.refresh_listbox()
        self.select_all()
        self.main_window.log(f"📁 폴더에서 {len(self.app_state['image_files'])}개의 이미지를 불러왔습니다.")
        
    def refresh_listbox(self):
        # Save selection
        sel = self.listbox.curselection()
        
        self.listbox.delete(0, tk.END)
        
        if not hasattr(self.main_window, 'right_panel'):
            for f in self.app_state['image_files']:
                self.listbox.insert(tk.END, f)
            self.update_file_count()
            return
            
        mode = self.main_window.get_current_mode()
        if mode == 'compress':
            settings = self.main_window.get_compression_settings()
        else:
            settings = self.main_window.get_rename_settings()
            
        raw_name = settings['raw_name'].replace(" ", settings['separator']) if settings['raw_name'] else "이름없음"
        
        total_files = len(self.app_state['image_files'])
        for i, f in enumerate(self.app_state['image_files']):
            if mode == 'compress':
                new_f = f"{raw_name}{settings['separator']}{i+1}.webp"
            else:
                pad_val = settings.get('pad_mode', '자동')
                if pad_val == "지정안함": pad_length = 1
                elif pad_val == "자동": pad_length = len(str(total_files)) if total_files > 0 else 1
                elif pad_val == "2자리": pad_length = 2
                elif pad_val == "3자리": pad_length = 3
                elif pad_val == "4자리": pad_length = 4
                elif pad_val == "5자리": pad_length = 5
                elif pad_val == "6자리": pad_length = 6
                else: pad_length = 1
                
                idx_str = str(i + 1).zfill(pad_length)
                ext = os.path.splitext(f)[1] if settings['target_ext'] == "원본 유지" else settings['target_ext']
                new_f = f"{raw_name}{settings['separator']}{idx_str}{ext}"
                
            self.listbox.insert(tk.END, f"{f}  ➔  {new_f}")
            
        # Restore selection
        for i in sel:
            self.listbox.select_set(i)
            
        self.update_file_count()
        
    def select_all(self):
        self.listbox.select_set(0, tk.END)
        self.on_listbox_select()
        
    def deselect_all(self):
        self.listbox.selection_clear(0, tk.END)
        self.on_listbox_select()
        
    def on_listbox_select(self):
        self.update_file_count()
        self.main_window.on_selection_change()
        
    def update_file_count(self):
        total = len(self.app_state['image_files'])
        selected = len(self.listbox.curselection())
        self.lbl_file_count.configure(text=f"선택된 파일: {selected} / {total}개")
        
    def get_selected_files(self):
        indices = self.listbox.curselection()
        return [self.app_state['image_files'][i] for i in indices]
        
    def move_up(self):
        indices = list(self.listbox.curselection())
        if not indices: return
        
        for i in indices:
            if i > 0 and (i-1) not in indices:
                self.app_state['image_files'][i], self.app_state['image_files'][i-1] = self.app_state['image_files'][i-1], self.app_state['image_files'][i]
                
        self.refresh_listbox()
        # Reselect
        for i in indices:
            if i > 0 and (i-1) not in indices:
                self.listbox.select_set(i-1)
            else:
                self.listbox.select_set(i)
        self.on_listbox_select()
        
    def move_down(self):
        indices = list(self.listbox.curselection())
        if not indices: return
        
        max_idx = len(self.app_state['image_files']) - 1
        for i in reversed(indices):
            if i < max_idx and (i+1) not in indices:
                self.app_state['image_files'][i], self.app_state['image_files'][i+1] = self.app_state['image_files'][i+1], self.app_state['image_files'][i]
                
        self.refresh_listbox()
        # Reselect
        for i in reversed(indices):
            if i < max_idx and (i+1) not in indices:
                self.listbox.select_set(i+1)
            else:
                self.listbox.select_set(i)
        self.on_listbox_select()
        
    def remove_from_list(self):
        indices = list(self.listbox.curselection())
        if not indices: return
        
        for i in reversed(indices):
            del self.app_state['image_files'][i]
            
        self.refresh_listbox()
        self.main_window.log(f"🗑️ 목록에서 {len(indices)}개의 파일이 제외되었습니다.")
        self.on_listbox_select()
        
    def handle_rotate(self):
        indices = self.listbox.curselection()
        if not indices: return
        
        first_idx = indices[0]
        filename = self.app_state['image_files'][first_idx]
        filepath = os.path.join(self.app_state['selected_folder'], filename)
        
        current_rot = self.app_state['rotations'].get(filepath, 0)
        self.app_state['rotations'][filepath] = (current_rot - 90) % 360
        self.update_preview()
        
    def update_preview(self):
        selected_files = self.get_selected_files()
        if not selected_files:
            self.lbl_image.configure(image="", text="이미지 없음")
            self.lbl_info.configure(text="선택된 이미지 없음")
            self.btn_rotate.configure(state="disabled")
            self.current_preview_file = None
            return
            
        first_file = selected_files[0]
        filepath = os.path.join(self.app_state['selected_folder'], first_file)
        self.current_preview_file = filepath
        
        try:
            rot = self.app_state['rotations'].get(filepath, 0)
            
            # Load and rotate image using PIL
            with Image.open(filepath) as img:
                if rot != 0:
                    img = img.rotate(rot, expand=True)
                img.thumbnail((400, 400)) # resize for preview
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
                
            self.lbl_image.configure(image=ctk_img, text="")
            self.btn_rotate.configure(state="normal")
            
            orig_size = os.path.getsize(filepath)
            size_str = ImageProcessor.format_size(orig_size)
            
            comp_settings = self.main_window.get_compression_settings()
            preview_size_val = comp_settings.get('preview_size_val', False) if comp_settings else False
            compression_val = comp_settings.get('compression_method', '6') if comp_settings else '6'
            
            if not preview_size_val or self.main_window.get_current_mode() != 'compress':
                self.lbl_info.configure(text=f"{first_file} ({size_str})")
            else:
                self.lbl_info.configure(text=f"{first_file} ({size_str}) -> 예상 용량 계산 중...")
                
                def on_success(expected):
                    if self.current_preview_file == filepath:
                        self.lbl_info.configure(text=f"{first_file} ({size_str}) -> 약 {ImageProcessor.format_size(expected)}")
                        
                def on_error(err):
                    if self.current_preview_file == filepath:
                        self.lbl_info.configure(text=f"{first_file} ({size_str}) -> 계산 실패")
                        
                ImageProcessor.calculate_expected_size_async(filepath, rot, compression_val, on_success, on_error)
                
        except Exception as e:
            self.lbl_image.configure(image="", text="미리보기 실패")
            self.lbl_info.configure(text=f"{first_file} (미리보기 실패)")
            self.btn_rotate.configure(state="disabled")
            
    def set_run_state(self, is_running):
        state = "disabled" if is_running else "normal"
        self.btn_open_folder.configure(state=state)
        self.listbox.configure(state=tk.DISABLED if is_running else tk.NORMAL)
