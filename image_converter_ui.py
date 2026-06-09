import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import threading
from datetime import datetime
import webbrowser
import send2trash

class ImageConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("이미지 변환 & 이름 변경 프로그램 v2 (WebP)")
        self.root.geometry("1200x1000")
        
        self.selected_folder = ""
        self.image_files = []
        self.rotations = {}
        self.preview_image_ref = None # 가비지 컬렉션 방지용
        
        self.setup_ui()

    def setup_ui(self):
        style = ttk.Style()
        style.configure("TButton", padding=5)
        
        # 푸터를 먼저 생성하여 메인 창 크기에 밀리지 않도록 고정
        self.setup_footer()
        
        # 메인 PanedWindow (좌우 분할)
        self.paned_window = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 좌측: 제어부
        self.left_frame = ttk.Frame(self.paned_window)
        # 우측: 정보부
        self.right_frame = ttk.Frame(self.paned_window)
        
        self.paned_window.add(self.left_frame, weight=1)
        self.paned_window.add(self.right_frame, weight=1)
        
        self.setup_left_panel()
        self.setup_right_panel()

    def setup_footer(self):
        footer_frame = ttk.Frame(self.root)
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=5)
        
        # 깃허브 주소 라벨 (클릭 시 이동)
        lbl_github = tk.Label(footer_frame, text="GitHub: https://github.com/rinology", fg="blue", cursor="hand2", font=("Consolas", 9, "underline"))
        lbl_github.pack(side=tk.LEFT)
        lbl_github.bind("<Button-1>", lambda e: webbrowser.open_new("https://github.com/rinology"))
        
        # 닉네임 라벨
        lbl_nickname = tk.Label(footer_frame, text="Made by rinology", fg="gray", font=("Consolas", 9))
        lbl_nickname.pack(side=tk.RIGHT)

    def setup_left_panel(self):
        # 1. 폴더 선택 섹션
        folder_frame = ttk.LabelFrame(self.left_frame, text="1. 폴더 선택", padding=10)
        folder_frame.pack(fill=tk.X, pady=(0, 5))
        
        btn_select_folder = ttk.Button(folder_frame, text="폴더 열기", command=self.select_folder)
        btn_select_folder.pack(side=tk.LEFT, padx=(0, 10))
        
        self.lbl_folder_path = ttk.Label(folder_frame, text="선택된 폴더 없음", foreground="gray")
        self.lbl_folder_path.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 2. 파일 리스트 섹션
        list_frame = ttk.LabelFrame(self.left_frame, text="2. 이미지 파일 목록 (순서 변경 및 선택)", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 상태 표시줄 (선택 개수)
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

        # 3. 변환 설정 섹션
        settings_frame = ttk.LabelFrame(self.left_frame, text="3. 변환 설정", padding=10)
        settings_frame.pack(fill=tk.X, pady=5)
        
        # 이름 지정
        name_frame = ttk.Frame(settings_frame)
        name_frame.pack(fill=tk.X, pady=2)
        ttk.Label(name_frame, text="변경할 이름 (영문):").pack(side=tk.LEFT)
        self.entry_basename_var = tk.StringVar(value="my image")
        self.entry_basename = ttk.Entry(name_frame, textvariable=self.entry_basename_var, width=20, exportselection=False)
        self.entry_basename.pack(side=tk.LEFT, padx=10)
        self.entry_basename_var.trace_add("write", self.update_name_preview)
        
        # 연결 기호
        sep_frame = ttk.Frame(settings_frame)
        sep_frame.pack(fill=tk.X, pady=2)
        ttk.Label(sep_frame, text="이름 연결 기호:").pack(side=tk.LEFT)
        self.separator_var = tk.StringVar(value="_")
        ttk.Radiobutton(sep_frame, text="_ (언더바)", variable=self.separator_var, value="_", command=self.update_name_preview).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(sep_frame, text="- (하이픈)", variable=self.separator_var, value="-", command=self.update_name_preview).pack(side=tk.LEFT, padx=5)
        
        hint_label = ttk.Label(settings_frame, text="* 띄어쓰기 입력 시 위의 이름 연결 기호로 대체됩니다.", foreground="gray", font=("Consolas", 8))
        hint_label.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # 이름 미리보기
        preview_frame = ttk.Frame(settings_frame)
        preview_frame.pack(fill=tk.X, pady=2)
        ttk.Label(preview_frame, text="적용 예시:", foreground="blue").pack(side=tk.LEFT)
        self.lbl_name_preview = ttk.Label(preview_frame, text="", font=("Consolas", 10, "bold"), foreground="blue")
        self.lbl_name_preview.pack(side=tk.LEFT, padx=10)
        self.update_name_preview() # 초기화

        # 저장 위치
        self.loc_frame = ttk.Frame(settings_frame)
        self.loc_frame.pack(fill=tk.X, pady=5)
        ttk.Label(self.loc_frame, text="저장 위치:").pack(side=tk.LEFT)
        self.save_loc_var = tk.StringVar(value="sub")
        ttk.Radiobutton(self.loc_frame, text="현재 폴더", variable=self.save_loc_var, value="same", command=self.toggle_subfolder_options).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(self.loc_frame, text="하위 폴더", variable=self.save_loc_var, value="sub", command=self.toggle_subfolder_options).pack(side=tk.LEFT, padx=5)
        
        # 하위 폴더 옵션 (숨김/표시 전환용)
        self.subfolder_frame = ttk.Frame(settings_frame)
        self.subfolder_frame.pack(fill=tk.X, pady=2) # 기본적으로 하위 폴더이므로 보임
        
        ttk.Label(self.subfolder_frame, text="폴더명:").pack(side=tk.LEFT)
        self.subfolder_name_var = tk.StringVar(value="output")
        ttk.Entry(self.subfolder_frame, textvariable=self.subfolder_name_var, width=10, exportselection=False).pack(side=tk.LEFT, padx=5)
        
        self.date_prefix_var = tk.StringVar(value="datetime")
        ttk.Radiobutton(self.subfolder_frame, text="년월일시", variable=self.date_prefix_var, value="datetime").pack(side=tk.LEFT)
        ttk.Radiobutton(self.subfolder_frame, text="년월일", variable=self.date_prefix_var, value="date").pack(side=tk.LEFT)
        ttk.Radiobutton(self.subfolder_frame, text="사용안함", variable=self.date_prefix_var, value="none").pack(side=tk.LEFT)

        # 원본 유지/삭제
        orig_frame = ttk.Frame(settings_frame)
        orig_frame.pack(fill=tk.X, pady=5)
        ttk.Label(orig_frame, text="원본 파일:").pack(side=tk.LEFT)
        self.original_var = tk.StringVar(value="keep")
        ttk.Radiobutton(orig_frame, text="유지", variable=self.original_var, value="keep").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(orig_frame, text="삭제", variable=self.original_var, value="delete").pack(side=tk.LEFT, padx=5)

        # 압축 강도
        comp_frame = ttk.Frame(settings_frame)
        comp_frame.pack(fill=tk.X, pady=5)
        ttk.Label(comp_frame, text="압축 강도:").pack(side=tk.LEFT)
        self.compression_var = tk.StringVar(value="6")
        ttk.Radiobutton(comp_frame, text="최대(느림/최소)", variable=self.compression_var, value="6", command=self.update_expected_size).pack(side=tk.LEFT, padx=2)
        ttk.Radiobutton(comp_frame, text="일반(적정)", variable=self.compression_var, value="4", command=self.update_expected_size).pack(side=tk.LEFT, padx=2)
        ttk.Radiobutton(comp_frame, text="빠름(용량증가)", variable=self.compression_var, value="0", command=self.update_expected_size).pack(side=tk.LEFT, padx=2)
        
        # 예상 용량 계산 옵션
        self.preview_size_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(comp_frame, text="예상 용량 계산 (느려짐)", variable=self.preview_size_var, command=self.update_expected_size).pack(side=tk.LEFT, padx=10)

        # 4. 실행 섹션
        run_frame = ttk.Frame(self.left_frame)
        run_frame.pack(fill=tk.X, pady=10)
        
        self.btn_run = ttk.Button(run_frame, text="🚀 변환 실행", command=self.start_conversion)
        self.btn_run.pack(fill=tk.X, ipady=10)

    def setup_right_panel(self):
        # 1. 썸네일 미리보기 영역
        preview_group = ttk.LabelFrame(self.right_frame, text="이미지 미리보기", padding=10)
        preview_group.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        self.lbl_image_preview = tk.Label(preview_group, text="리스트에서 이미지를 선택하면\n여기에 미리보기가 표시됩니다.", bg="lightgray", justify=tk.CENTER)
        self.lbl_image_preview.pack(fill=tk.BOTH, expand=True, pady=5)
        
        info_frame = ttk.Frame(preview_group)
        info_frame.pack(fill=tk.X, pady=5)
        
        self.lbl_image_info = ttk.Label(info_frame, text="")
        self.lbl_image_info.pack(side=tk.LEFT, padx=10, expand=True)
        
        self.btn_rotate = ttk.Button(info_frame, text="⟳ 90도 회전", command=self.rotate_current_image, state=tk.DISABLED)
        self.btn_rotate.pack(side=tk.RIGHT, padx=10)

        # 2. 진행 상태 및 로그 영역
        log_group = ttk.LabelFrame(self.right_frame, text="진행 상태 및 로그", padding=10)
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

    def format_size(self, size_bytes):
        if size_bytes < 1024:
            return f"{size_bytes}B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes/1024:.1f}KB"
        else:
            return f"{size_bytes/(1024*1024):.2f}MB"

    def log(self, message):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def update_name_preview(self, *args):
        raw_name = self.entry_basename_var.get().strip()
        sep = self.separator_var.get()
        # 띄어쓰기를 연결 기호로 변경
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

    def select_folder(self):
        folder = filedialog.askdirectory(title="이미지가 있는 폴더를 선택하세요")
        if folder:
            self.selected_folder = folder
            self.lbl_folder_path.config(text=self.selected_folder, foreground="black")
            self.load_images()

    def load_images(self):
        self.listbox.delete(0, tk.END)
        self.image_files = []
        self.rotations = {}
        valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp')
        
        for f in os.listdir(self.selected_folder):
            if f.lower().endswith(valid_extensions):
                self.image_files.append(f)
                self.listbox.insert(tk.END, f)
        
        self.log(f"📁 폴더에서 {len(self.image_files)}개의 이미지를 불러왔습니다.")
        self.select_all()

    def select_all(self):
        self.listbox.select_set(0, tk.END)
        self.update_file_count_label()
        self.on_listbox_select()

    def deselect_all(self):
        self.listbox.selection_clear(0, tk.END)
        self.update_file_count_label()
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
        # 삭제는 뒤에서부터 해야 인덱스가 꼬이지 않음
        for pos in reversed(selected_indices):
            filename = self.listbox.get(pos)
            self.listbox.delete(pos)
            if filename in self.image_files:
                self.image_files.remove(filename)
                removed_count += 1
                
        if removed_count > 0:
            self.log(f"🗑️ 목록에서 {removed_count}개의 파일이 제외되었습니다.")
                
        self.update_file_count_label()
        self.on_listbox_select()

    def on_listbox_select(self, event=None):
        self.update_file_count_label()
        
        selected_indices = self.listbox.curselection()
        if not selected_indices:
            self.lbl_image_preview.config(image='', text="선택된 이미지가 없습니다.", bg="lightgray")
            self.lbl_image_info.config(text="")
            self.btn_rotate.config(state=tk.DISABLED)
            self.preview_image_ref = None
            return
            
        self.btn_rotate.config(state=tk.NORMAL)
        
        # 첫 번째 선택된 이미지 표시
        first_selected_idx = selected_indices[0]
        filename = self.listbox.get(first_selected_idx)
        filepath = os.path.join(self.selected_folder, filename)
        
        try:
            img = Image.open(filepath)
            rot = self.rotations.get(filepath, 0)
            if rot != 0:
                img = img.rotate(rot, expand=True)
                
            # 썸네일 생성 (비율 유지하며 최대 550x550)
            img.thumbnail((550, 550))
            photo = ImageTk.PhotoImage(img)
            
            self.lbl_image_preview.config(image=photo, text="", bg="SystemButtonFace")
            self.preview_image_ref = photo # 가비지 컬렉션 방지
            
            self.update_expected_size()
        except Exception as e:
            self.lbl_image_preview.config(image='', text="미리보기를 불러올 수 없습니다.", bg="lightgray")
            self.lbl_image_info.config(text=filename)

    def update_expected_size(self, *args):
        selected_indices = self.listbox.curselection()
        if not selected_indices: return
        
        filename = self.listbox.get(selected_indices[0])
        filepath = os.path.join(self.selected_folder, filename)
        
        try:
            orig_size = os.path.getsize(filepath)
            size_str = self.format_size(orig_size)
        except Exception:
            return
            
        if not self.preview_size_var.get():
            self.lbl_image_info.config(text=f"{filename} ({size_str})")
            return
            
        self.lbl_image_info.config(text=f"{filename} ({size_str}) -> 예상 변환 용량: 계산 중...")
        
        def calc():
            try:
                method_val = int(self.compression_var.get())
                from io import BytesIO
                with Image.open(filepath) as img:
                    rot = self.rotations.get(filepath, 0)
                    if rot != 0:
                        img = img.rotate(rot, expand=True)
                    if img.mode in ("RGBA", "P"):
                        img = img.convert("RGB")
                    
                    buffer = BytesIO()
                    img.save(buffer, format="webp", quality=80, method=method_val)
                    expected = len(buffer.getvalue())
                
                self.root.after(0, lambda: self.lbl_image_info.config(
                    text=f"{filename} ({size_str}) -> 예상 변환 용량: 약 {self.format_size(expected)}"
                ))
            except:
                self.root.after(0, lambda: self.lbl_image_info.config(text=f"{filename} ({size_str}) -> 예상 용량 계산 실패"))
        
        threading.Thread(target=calc, daemon=True).start()

    def rotate_current_image(self):
        selected_indices = self.listbox.curselection()
        if not selected_indices: return
        filename = self.listbox.get(selected_indices[0])
        filepath = os.path.join(self.selected_folder, filename)
        
        current_rot = self.rotations.get(filepath, 0)
        self.rotations[filepath] = (current_rot - 90) % 360 # 시계 방향으로 90도 회전
        
        self.on_listbox_select()

    def start_conversion(self):
        if not self.selected_folder:
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

        threading.Thread(target=self.process_images, args=(selected_indices, raw_name), daemon=True).start()

    def process_images(self, selected_indices, raw_name):
        self.btn_run.config(state=tk.DISABLED)
        self.log("🚀 변환 작업을 시작합니다...")
        self.progress_var.set(0)
        
        total_files = len(selected_indices)
        sep = self.separator_var.get()
        base_name = raw_name.replace(" ", sep)
        
        save_loc = self.save_loc_var.get()
        delete_orig = self.original_var.get() == "delete"
        
        output_dir = self.selected_folder
        if save_loc == "sub":
            prefix_opt = self.date_prefix_var.get()
            sub_name = self.subfolder_name_var.get().strip()
            
            now = datetime.now()
            prefix = ""
            if prefix_opt == "datetime":
                prefix = now.strftime("%Y%m%d_%H%M%S") + "_"
            elif prefix_opt == "date":
                prefix = now.strftime("%Y%m%d") + "_"
                
            folder_name = f"{prefix}{sub_name}" if sub_name else prefix.rstrip("_")
            if not folder_name:
                folder_name = "output"
                
            output_dir = os.path.join(self.selected_folder, folder_name)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                self.log(f"📂 폴더 생성됨: {output_dir}")

        success_count = 0
        error_count = 0
        total_saved_bytes = 0
        
        for i, pos in enumerate(selected_indices):
            idx = i + 1 # 1부터 시작
            filename = self.listbox.get(pos)
            filepath = os.path.join(self.selected_folder, filename)
            
            new_filename = f"{base_name}{sep}{idx}.webp"
            new_filepath = os.path.join(output_dir, new_filename)
            
            try:
                orig_size = os.path.getsize(filepath)
                
                with Image.open(filepath) as img:
                    rot = self.rotations.get(filepath, 0)
                    if rot != 0:
                        img = img.rotate(rot, expand=True)
                    if img.mode in ("RGBA", "P"):
                        img = img.convert("RGB")
                    method_val = int(self.compression_var.get())
                    img.save(new_filepath, "webp", quality=80, method=method_val)
                
                new_size = os.path.getsize(new_filepath)
                size_diff = orig_size - new_size
                if size_diff > 0:
                    total_saved_bytes += size_diff
                
                log_msg = f"✅ [{idx}/{total_files}] {filename} -> {new_filename} "
                log_msg += f"(용량: {self.format_size(orig_size)} -> {self.format_size(new_size)})"
                self.log(log_msg)
                
                if delete_orig and filepath != new_filepath:
                    send2trash.send2trash(filepath)
                    self.log(f"   🗑️ 원본이 휴지통으로 이동됨: {filename}")
                    
                success_count += 1
            except Exception as e:
                self.log(f"❌ [에러] {filename} 변환 실패: {e}")
                error_count += 1
                
            # 진행률 업데이트
            progress = (idx / total_files) * 100
            self.progress_var.set(progress)
            self.lbl_progress_text.config(text=f"진행 상태: {idx} / {total_files} 완료")
            self.root.update_idletasks()
                
        self.log(f"🎉 작업 완료! (성공: {success_count}, 에러: {error_count})")
        if total_saved_bytes > 0:
            self.log(f"💾 총 절감된 용량: {self.format_size(total_saved_bytes)}")
        self.btn_run.config(state=tk.NORMAL)

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageConverterApp(root)
    root.mainloop()
