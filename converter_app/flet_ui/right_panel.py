import flet as ft
import os
from converter_app.core.image_processor import ImageProcessor
from converter_app.flet_ui.rename_dialog import RenameDialog

class RightPanel(ft.Container):
    def __init__(self, page, app_state, main_window):
        super().__init__(expand=True)
        self.app_page = page
        self.app_state = app_state
        self.main_window = main_window
        self.content = self.build_ui()

    def build_ui(self):
        # 1. Settings (Top Right)
        self.mode_selector = ft.SegmentedButton(
            segments=[
                ft.Segment(value="compress", label=ft.Text("압축 및 이름변경"), icon=ft.Icons.COMPRESS),
                ft.Segment(value="rename", label=ft.Text("단순 이름변경"), icon=ft.Icons.DRIVE_FILE_RENAME_OUTLINE)
            ],
            selected=["compress"],
            on_change=self.on_mode_change
        )
        
        self.build_compress_tab()
        self.build_rename_tab()
        
        self.tab_container = ft.Container(
            content=self.tab_compress,
            expand=True,
            padding=5
        )
        
        self.btn_run = ft.ElevatedButton(
            "🚀 변환 실행", 
            style=ft.ButtonStyle(bgcolor=ft.Colors.PRIMARY, color=ft.Colors.ON_PRIMARY, padding=20),
            on_click=self.start_conversion
        )
        
        settings_frame = ft.Container(
            content=ft.Column([
                ft.Row([self.mode_selector], alignment=ft.MainAxisAlignment.CENTER),
                ft.Divider(),
                self.tab_container,
                ft.Row([self.btn_run], alignment=ft.MainAxisAlignment.CENTER)
            ], expand=True),
            expand=True, border=ft.Border.all(1, ft.Colors.OUTLINE), border_radius=8, padding=10
        )
        
        # 2. Log & Progress (Bottom Right)
        self.progress_bar = ft.ProgressBar(value=0, visible=False)
        self.lbl_progress = ft.Text("대기 중...")
        self.log_list = ft.ListView(expand=True, spacing=5, auto_scroll=True)
        
        credits = ft.Row([
            ft.Text("Developed by ", size=12, color=ft.Colors.ON_SURFACE_VARIANT),
            ft.Text("Taerin", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE),
            ft.Text(" | ", size=12, color=ft.Colors.ON_SURFACE_VARIANT),
            ft.Text("GitHub", size=12, color=ft.Colors.BLUE, tooltip="https://github.com/Taerin") 
        ], alignment=ft.MainAxisAlignment.END)
        
        log_frame = ft.Container(
            content=ft.Column([
                ft.Text("진행 상태 및 로그", weight=ft.FontWeight.BOLD),
                self.progress_bar,
                self.lbl_progress,
                ft.Container(content=self.log_list, expand=True, bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST, border_radius=5, padding=5),
                credits
            ]),
            expand=True, border=ft.Border.all(1, ft.Colors.OUTLINE), border_radius=8, padding=10
        )
        
        return ft.Column([
            settings_frame,
            log_frame
        ], expand=True)

    def on_mode_change(self, e):
        selected_mode = list(self.mode_selector.selected)[0]
        if selected_mode == "compress":
            self.tab_container.content = self.tab_compress
        else:
            self.tab_container.content = self.tab_rename
        self.app_page.update()
        self.main_window.on_settings_change()

    def build_compress_tab(self):
        self.c_name_input = ft.TextField(label="변경할 이름 (영문)", value="my image", width=200, on_change=self.update_c_preview)
        self.c_sep_rg = ft.RadioGroup(content=ft.Row([ft.Radio(value="_", label="_ (언더바)"), ft.Radio(value="-", label="- (하이픈)")]), value="_", on_change=self.update_c_preview)
        self.c_preview_lbl = ft.Text("", color=ft.Colors.BLUE, weight=ft.FontWeight.BOLD)
        
        self.c_save_loc = ft.RadioGroup(content=ft.Row([ft.Radio(value="same", label="현재 폴더"), ft.Radio(value="sub", label="하위 폴더")]), value="sub", on_change=self.toggle_c_subfolder)
        self.c_sub_name = ft.TextField(label="폴더명", value="output", width=120)
        self.c_date_prefix = ft.Dropdown(options=[ft.dropdown.Option("datetime", "년월일시"), ft.dropdown.Option("date", "년월일"), ft.dropdown.Option("none", "사용안함")], value="datetime", width=120)
        self.c_sub_row = ft.Row([self.c_sub_name, self.c_date_prefix])
        
        self.c_orig = ft.RadioGroup(content=ft.Row([ft.Radio(value="keep", label="유지"), ft.Radio(value="delete", label="삭제")]), value="keep")
        self.c_comp = ft.Dropdown(options=[ft.dropdown.Option("6", "최대(느림)"), ft.dropdown.Option("4", "일반(적정)"), ft.dropdown.Option("0", "빠름")], value="6", width=150, label="압축 강도", on_select=lambda e: self.main_window.on_settings_change())
        self.c_preview_size = ft.Switch(label="예상 용량 계산 (느려짐)", value=False, on_change=lambda e: self.main_window.on_settings_change())
        
        self.tab_compress = ft.Column([
            ft.Row([self.c_name_input, ft.Text("이름 연결 기호:"), self.c_sep_rg]),
            ft.Row([ft.Text("적용 예시:", color=ft.Colors.BLUE), self.c_preview_lbl]),
            ft.Row([ft.Text("저장 위치:"), self.c_save_loc, self.c_sub_row]),
            ft.Row([ft.Text("원본 파일:"), self.c_orig, self.c_comp, self.c_preview_size])
        ], scroll=ft.ScrollMode.AUTO, expand=True)
        self.update_c_preview(None)
        
    def build_rename_tab(self):
        self.r_name_input = ft.TextField(label="변경할 이름", value="사진 고양이", width=200, on_change=self.update_r_preview)
        self.r_sep_rg = ft.RadioGroup(content=ft.Row([ft.Radio(value="_", label="_ (언더바)"), ft.Radio(value="-", label="- (하이픈)")]), value="-", on_change=self.update_r_preview)
        self.r_preview_lbl = ft.Text("", color=ft.Colors.BLUE, weight=ft.FontWeight.BOLD)
        
        self.r_pad = ft.Dropdown(options=[ft.dropdown.Option(x) for x in ["지정안함", "자동", "2자리", "3자리", "4자리", "5자리", "6자리"]], value="자동", width=120, label="숫자 패딩", on_select=self.update_r_preview)
        self.r_ext = ft.Dropdown(options=[ft.dropdown.Option(x) for x in ["원본 유지", ".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"]], value="원본 유지", width=120, label="확장자", on_select=self.update_r_preview)
        
        self.r_save_loc = ft.RadioGroup(content=ft.Row([ft.Radio(value="same", label="현재 폴더"), ft.Radio(value="sub", label="하위 폴더")]), value="sub", on_change=self.toggle_r_subfolder)
        self.r_sub_name = ft.TextField(label="폴더명", value="renamed", width=120)
        self.r_date_prefix = ft.Dropdown(options=[ft.dropdown.Option("datetime", "년월일시"), ft.dropdown.Option("date", "년월일"), ft.dropdown.Option("none", "사용안함")], value="none", width=120)
        self.r_sub_row = ft.Row([self.r_sub_name, self.r_date_prefix])
        
        self.r_orig = ft.RadioGroup(content=ft.Row([ft.Radio(value="keep", label="유지 (복사)"), ft.Radio(value="delete", label="삭제 (이동)")]), value="keep")
        
        self.tab_rename = ft.Column([
            ft.Row([self.r_name_input, ft.Text("이름 연결 기호:"), self.r_sep_rg]),
            ft.Row([self.r_pad, self.r_ext]),
            ft.Row([ft.Text("적용 예시:", color=ft.Colors.BLUE), self.r_preview_lbl]),
            ft.Row([ft.Text("저장 위치:"), self.r_save_loc, self.r_sub_row]),
            ft.Row([ft.Text("원본 파일:"), self.r_orig])
        ], scroll=ft.ScrollMode.AUTO, expand=True)
        self.update_r_preview(None)

    def update_c_preview(self, e):
        raw_name = self.c_name_input.value.strip()
        sep = self.c_sep_rg.value
        processed = raw_name.replace(" ", sep) if raw_name else "이름없음"
        self.c_preview_lbl.value = f"{processed}{sep}1.webp"
        self.app_page.update()
        
    def toggle_c_subfolder(self, e):
        self.c_sub_row.visible = (self.c_save_loc.value == "sub")
        self.app_page.update()
        
    def update_r_preview(self, e):
        raw_name = self.r_name_input.value.strip()
        sep = self.r_sep_rg.value
        processed = raw_name.replace(" ", sep) if raw_name else "이름없음"
        
        pad_val = self.r_pad.value
        if pad_val == "지정안함": pad = "1"
        elif pad_val in ["자동", "2자리"]: pad = "01"
        elif pad_val == "3자리": pad = "001"
        elif pad_val == "4자리": pad = "0001"
        elif pad_val == "5자리": pad = "00001"
        elif pad_val == "6자리": pad = "000001"
        else: pad = "1"
        
        ext = ".확장자" if self.r_ext.value == "원본 유지" else self.r_ext.value
        self.r_preview_lbl.value = f"{processed}{sep}{pad}{ext}"
        self.app_page.update()
        
    def toggle_r_subfolder(self, e):
        self.r_sub_row.visible = (self.r_save_loc.value == "sub")
        self.app_page.update()

    def get_current_mode(self):
        return list(self.mode_selector.selected)[0]

    def get_compression_settings(self):
        return {
            'mode': 'compress',
            'raw_name': self.c_name_input.value.strip(),
            'separator': self.c_sep_rg.value,
            'save_location': self.c_save_loc.value,
            'subfolder_name': self.c_sub_name.value.strip(),
            'date_prefix': self.c_date_prefix.value,
            'delete_orig': self.c_orig.value == "delete",
            'compression_method': self.c_comp.value,
            'preview_size_val': self.c_preview_size.value
        }

    def get_rename_settings(self):
        return {
            'mode': 'rename',
            'raw_name': self.r_name_input.value.strip(),
            'separator': self.r_sep_rg.value,
            'save_location': self.r_save_loc.value,
            'subfolder_name': self.r_sub_name.value.strip(),
            'date_prefix': self.r_date_prefix.value,
            'delete_orig': self.r_orig.value == "delete",
            'pad_mode': self.r_pad.value,
            'target_ext': self.r_ext.value
        }

    def log(self, message):
        self.log_list.controls.append(ft.Text(message, size=12, selectable=True))
        self.app_page.update()

    def update_progress(self, current, total):
        if not self.progress_bar.visible:
            self.progress_bar.visible = True
        progress = (current / total) if total > 0 else 0
        self.progress_bar.value = progress
        self.lbl_progress.value = f"진행 상태: {current} / {total} 완료"
        if current == total and total > 0:
            self.lbl_progress.value = "완료!"
        self.app_page.update()

    def set_run_state(self, is_running):
        self.btn_run.disabled = is_running
        self.mode_selector.disabled = is_running
        
    def show_snack(self, message):
        self.app_page.snack_bar = ft.SnackBar(ft.Text(message))
        self.app_page.snack_bar.open = True
        self.app_page.update()

    def start_conversion(self, e):
        if not self.app_state.get('selected_folder'):
            return self.show_snack("먼저 폴더를 선택해주세요.")
            
        selected_files = self.main_window.get_selected_files()
        if not selected_files:
            return self.show_snack("처리할 이미지를 선택해주세요.")

        mode = self.get_current_mode()
        
        if mode == 'compress':
            settings = self.get_compression_settings()
            if not settings['raw_name']: return self.show_snack("변경할 영문 이름을 입력해주세요.")
            self.execute_run(selected_files, settings)
        else:
            settings = self.get_rename_settings()
            if not settings['raw_name']: return self.show_snack("변경할 이름을 입력해주세요.")
            
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
                
            dialog = RenameDialog(selected_files, new_names, on_confirm)
            self.app_page.overlay.append(dialog)
            dialog.open = True
            self.app_page.update()

    def execute_run(self, selected_files, settings):
        self.main_window.set_run_state(True)
        self.progress_bar.value = 0
        self.progress_bar.visible = True
        self.lbl_progress.value = "진행 중..."
        self.app_page.update()
        
        def log_cb(msg):
            self.main_window.log(msg)
            
        def progress_cb(current, total):
            self.app_page.pubsub.send_all(("progress", current, total))
            
        callbacks = {
            'log': lambda m: self.app_page.run_thread(log_cb, m),
            'progress': lambda c, t: self.app_page.run_thread(progress_cb, c, t),
            'done': lambda s, e, b: self.app_page.run_thread(self.on_run_done)
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

    def on_run_done(self):
        self.main_window.set_run_state(False)
