import os
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from PIL import Image
import customtkinter as ctk
import threading
from converter_app.core.image_processor import ImageProcessor
from converter_app.utils.naming_utils import generate_new_filename

class LeftPanel(ctk.CTkFrame):
    def __init__(self, master, app_state, main_window):
        super().__init__(master)
        self.app_state = app_state
        self.main_window = main_window
        self.current_preview_file = None
        self.current_preview_rot = None
        self.cached_preview_ctk_img = None
        self.cached_preview_size_str = None
        self._drag_data = None
        
        self.app_state.add_observer(self.on_state_change)
        
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
        
        # Treeview styling
        style = ttk.Style(self)
        style.theme_use("clam")
        
        mode = ctk.get_appearance_mode()
        bg_color = "#2b2b2b" if mode == "Dark" else "#ffffff"
        fg_color = "white" if mode == "Dark" else "black"
        heading_bg = "#333333" if mode == "Dark" else "#e0e0e0"
        active_heading = "#444444" if mode == "Dark" else "#d0d0d0"
        
        style.configure("Treeview",
                        background=bg_color,
                        foreground=fg_color,
                        rowheight=25,
                        fieldbackground=bg_color,
                        borderwidth=1)
        style.map('Treeview', background=[('selected', '#1f538d')], foreground=[('selected', 'white')])
        style.configure("Treeview.Heading", background=heading_bg, foreground=fg_color, borderwidth=1)
        style.map("Treeview.Heading", background=[('active', active_heading)])

        self.tree = ttk.Treeview(list_frame, columns=("no", "before", "after"), show="headings", selectmode="extended")
        self.tree.heading("no", text="순번")
        self.tree.heading("before", text="변경 전 (원본)")
        self.tree.heading("after", text="변경 후 (미리보기)")
        self.tree.column("no", width=60, anchor="center")
        self.tree.column("before", width=150, anchor="w")
        self.tree.column("after", width=150, anchor="w")
        
        # User requested: Red for moving up, Blue for moving down
        self.tree.tag_configure("moved_up", foreground="#d90000" if mode == "Light" else "#ff4d4d")
        self.tree.tag_configure("moved_down", foreground="#0055ff" if mode == "Light" else "#4da6ff")
        self.tree.tag_configure("normal", foreground=fg_color)
        
        self.tree.grid(row=1, column=0, padx=(10, 5), pady=10, sticky="nsew")
        self.tree.bind('<<TreeviewSelect>>', lambda e: self.on_listbox_select())
        self.tree.bind('<ButtonPress-1>', self.on_drag_start)
        self.tree.bind('<B1-Motion>', self.on_drag_motion)
        self.tree.bind('<ButtonRelease-1>', self.on_drag_release)
        
        scrollbar = ctk.CTkScrollbar(list_frame, command=self.tree.yview)
        scrollbar.grid(row=1, column=1, padx=(0, 5), pady=10, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)
        
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
        
    def on_state_change(self, event, **kwargs):
        if event == "files_updated":
            self.lbl_folder_path.configure(text=self.app_state.selected_folder, text_color=("black", "white"))
            self.refresh_listbox(full_reload=True)
            self.select_all()
        elif event in ["files_reordered", "files_removed"]:
            self.refresh_listbox(full_reload=True)
        elif event == "rotation_updated":
            self.update_preview()

    def on_open_folder(self):
        path = filedialog.askdirectory(title="이미지가 있는 폴더를 선택하세요")
        if path:
            self.on_folder_selected(path)
            
    def on_folder_selected(self, path):
        valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp')
        files = []
        try:
            for f in os.listdir(path):
                if f.lower().endswith(valid_extensions):
                    files.append(f)
        except Exception:
            pass
            
        self.app_state.update_files(path, files)
        self.main_window.log(f"📁 폴더에서 {len(files)}개의 이미지를 불러왔습니다.")
        
    def refresh_listbox(self, full_reload=False):
        current_children = self.tree.get_children()
        total_files = len(self.app_state.image_files)
        
        if not hasattr(self.main_window, 'right_panel'):
            if full_reload:
                self.tree.delete(*current_children)
                for i, f in enumerate(self.app_state.image_files):
                    old_idx = self.app_state.original_files.index(f) + 1 if f in self.app_state.original_files else i + 1
                    new_idx = i + 1
                    tag = "normal"
                    if new_idx < old_idx:
                        tag = "moved_up"
                    elif new_idx > old_idx:
                        tag = "moved_down"
                        
                    self.tree.insert("", tk.END, values=(str(new_idx), f, ""), tags=(tag,))
            self.update_file_count()
            return
            
        mode = self.main_window.get_current_mode()
        if mode == 'compress':
            settings = self.main_window.get_compression_settings()
            settings['mode'] = 'compress'
        else:
            settings = self.main_window.get_rename_settings()
            settings['mode'] = 'rename'
            
        fast_update = (len(current_children) == total_files) and not full_reload
        if not fast_update:
            selected_indices = [current_children.index(iid) for iid in self.tree.selection()]
            self.tree.delete(*current_children)
            
        for i, f in enumerate(self.app_state.image_files):
            new_f = generate_new_filename(f, i + 1, settings, total_files)
            
            old_idx = self.app_state.original_files.index(f) + 1 if f in self.app_state.original_files else i + 1
            new_idx = i + 1
            tag = "normal"
            if new_idx < old_idx:
                tag = "moved_up"
            elif new_idx > old_idx:
                tag = "moved_down"
                
            if fast_update:
                self.tree.item(current_children[i], values=(str(new_idx), f, new_f), tags=(tag,))
            else:
                self.tree.insert("", tk.END, values=(str(new_idx), f, new_f), tags=(tag,))
                
        if not fast_update:
            new_children = self.tree.get_children()
            # Selection restoration logic - avoid restoring if files were just moved by user
            if not getattr(self, '_skip_restore_selection', False):
                for idx in selected_indices:
                    if idx < len(new_children):
                        self.tree.selection_add(new_children[idx])
            self._skip_restore_selection = False
            
        self.update_file_count()
        
    def select_all(self):
        self.tree.selection_set(self.tree.get_children())
        self.on_listbox_select()
        
    def deselect_all(self):
        self.tree.selection_remove(self.tree.get_children())
        self.on_listbox_select()
        
    def on_listbox_select(self):
        self.update_file_count()
        self.main_window.on_selection_change()
        # Preview update logic should be async to avoid lag
        self.update_preview()
        
    def update_file_count(self):
        total = len(self.app_state.image_files)
        selected = len(self.tree.selection())
        self.lbl_file_count.configure(text=f"선택된 파일: {selected} / {total}개")
        
    def get_selected_files(self):
        current_children = self.tree.get_children()
        indices = [current_children.index(iid) for iid in self.tree.selection()]
        return [self.app_state.image_files[i] for i in indices]
        
    def get_selected_indices(self):
        current_children = self.tree.get_children()
        return [current_children.index(iid) for iid in self.tree.selection()]

    def move_up(self):
        indices = self.get_selected_indices()
        if indices:
            self._skip_restore_selection = True
            self.app_state.move_files_up(indices)
            self._reselect_indices(indices, -1)
            
    def move_down(self):
        indices = self.get_selected_indices()
        if indices:
            self._skip_restore_selection = True
            self.app_state.move_files_down(indices)
            self._reselect_indices(indices, 1)
            
    def _reselect_indices(self, original_indices, shift):
        self.tree.selection_remove(self.tree.selection())
        new_children = self.tree.get_children()
        for i in original_indices:
            new_idx = i + shift
            if 0 <= new_idx < len(new_children) and (i + shift) not in original_indices:
                self.tree.selection_add(new_children[new_idx])
                self.tree.see(new_children[new_idx])
            else:
                self.tree.selection_add(new_children[i])
                self.tree.see(new_children[i])
        self.on_listbox_select()

    def on_drag_start(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            if item not in self.tree.selection():
                self.tree.selection_set(item)
            
            children = list(self.tree.get_children())
            self._drag_data = {
                'indices': [children.index(i) for i in self.tree.selection()]
            }

    def on_drag_motion(self, event):
        if getattr(self, '_drag_data', None):
            # Optional: Add visual feedback here
            pass

    def on_drag_release(self, event):
        if not getattr(self, '_drag_data', None):
            return
            
        target_item = self.tree.identify_row(event.y)
        if target_item:
            children = list(self.tree.get_children())
            target_index = children.index(target_item)
            indices = self._drag_data['indices']
            
            if target_index not in indices:
                self._skip_restore_selection = True
                self.app_state.move_files_to(indices, target_index)
                
                self.tree.selection_remove(self.tree.selection())
                new_children = self.tree.get_children()
                
                adjusted_target = target_index
                for i in indices:
                    if i < target_index:
                        adjusted_target -= 1
                        
                for j in range(len(indices)):
                    idx = adjusted_target + j
                    if 0 <= idx < len(new_children):
                        self.tree.selection_add(new_children[idx])
                        self.tree.see(new_children[idx])
                        
        self._drag_data = None
        self.on_listbox_select()

    def remove_from_list(self):
        indices = self.get_selected_indices()
        if indices:
            self.app_state.remove_files(indices)
            self.main_window.log(f"🗑️ 목록에서 {len(indices)}개의 파일이 제외되었습니다.")
        
    def handle_rotate(self):
        indices = self.get_selected_indices()
        if not indices: return
        
        first_idx = indices[0]
        filename = self.app_state.image_files[first_idx]
        filepath = os.path.join(self.app_state.selected_folder, filename)
        
        current_rot = self.app_state.get_rotation(filepath)
        self.app_state.set_rotation(filepath, (current_rot - 90) % 360)
        
    def update_preview(self):
        selected_files = self.get_selected_files()
        if not selected_files:
            self.lbl_image.configure(image="", text="이미지 없음")
            self.lbl_info.configure(text="선택된 이미지 없음")
            self.btn_rotate.configure(state="disabled")
            self.current_preview_file = None
            return
            
        first_file = selected_files[0]
        filepath = os.path.join(self.app_state.selected_folder, first_file)
        rot = self.app_state.get_rotation(filepath)
        
        if filepath != self.current_preview_file or rot != getattr(self, 'current_preview_rot', None):
            self.current_preview_file = filepath
            self.current_preview_rot = rot
            self.lbl_image.configure(image="", text="로딩 중...")
            
            def load_image_worker(target_path, target_rot):
                try:
                    with Image.open(target_path) as img:
                        if target_rot != 0:
                            img = img.rotate(target_rot, expand=True)
                        img.thumbnail((400, 400))
                        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
                        
                    orig_size = os.path.getsize(target_path)
                    size_str = ImageProcessor.format_size(orig_size)
                    self.after(0, self._apply_preview, target_path, target_rot, ctk_img, size_str, True)
                except Exception:
                    self.after(0, self._apply_preview, target_path, target_rot, None, "", False)
                    
            threading.Thread(target=load_image_worker, args=(filepath, rot), daemon=True).start()
        else:
            self._update_expected_size(first_file, filepath, rot)

    def _apply_preview(self, filepath, rot, ctk_img, size_str, success):
        if self.current_preview_file != filepath or self.current_preview_rot != rot:
            return # User selected another file before this finished
            
        first_file = os.path.basename(filepath)
        if success:
            self.cached_preview_ctk_img = ctk_img
            self.cached_preview_size_str = size_str
            self.lbl_image.configure(image=ctk_img, text="")
            self.btn_rotate.configure(state="normal")
            self._update_expected_size(first_file, filepath, rot)
        else:
            self.lbl_image.configure(image="", text="미리보기 실패")
            self.lbl_info.configure(text=f"{first_file} (미리보기 실패)")
            self.btn_rotate.configure(state="disabled")

    def _update_expected_size(self, first_file, filepath, rot):
        size_str = self.cached_preview_size_str
        
        comp_settings = self.main_window.get_compression_settings()
        preview_size_val = comp_settings.get('preview_size_val', False) if comp_settings else False
        compression_val = comp_settings.get('compression_method', '6') if comp_settings else '6'
        
        if not preview_size_val or self.main_window.get_current_mode() != 'compress':
            self.lbl_info.configure(text=f"{first_file} ({size_str})")
        else:
            self.lbl_info.configure(text=f"{first_file} ({size_str}) -> 예상 용량 계산 중...")
            
            def on_success(expected):
                if getattr(self, 'current_preview_file', None) == filepath:
                    self.lbl_info.configure(text=f"{first_file} ({size_str}) -> 약 {ImageProcessor.format_size(expected)}")
                    
            def on_error(err):
                if getattr(self, 'current_preview_file', None) == filepath:
                    self.lbl_info.configure(text=f"{first_file} ({size_str}) -> 계산 실패")
                    
            ImageProcessor.calculate_expected_size_async(filepath, rot, compression_val, on_success, on_error)
            
    def set_run_state(self, is_running):
        state = "disabled" if is_running else "normal"
        self.btn_open_folder.configure(state=state)
