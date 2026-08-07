import flet as ft
import os
from converter_app.core.image_processor import ImageProcessor
from converter_app.flet_ui.rename_dialog import RenameDialog

class LeftPanel(ft.Container):
    def __init__(self, page, app_state, on_selection_change, on_log, on_update_preview, on_run, on_file_rotated):
        super().__init__(expand=True)
        self.page = page
        self.app_state = app_state
        
        self.on_selection_change = on_selection_change
        self.on_log = on_log
        self.on_update_preview = on_update_preview
        self.on_run = on_run
        self.on_file_rotated = on_file_rotated
        
        # UI State
        self.selected_file_indices = set()
        self.preview_size_val = False
        self.compression_val = "6"
        self.content = self.build_ui()
        
    def build_ui(self):
        # 1. Folder Selection
        self.folder_picker = ft.FilePicker(on_result=self.on_folder_selected)
        self.page.overlay.append(self.folder_picker)
        
        self.lbl_folder_path = ft.Text("선택된 폴더 없음", color=ft.colors.ON_SURFACE_VARIANT, expand=True)
        folder_frame = ft.Container(
            content=ft.Row([
                ft.ElevatedButton("폴더 열기", icon=ft.icons.FOLDER_OPEN, on_click=lambda _: self.folder_picker.get_directory_path("이미지가 있는 폴더를 선택하세요")),
                self.lbl_folder_path
            ]),
            padding=10, border=ft.border.all(1, ft.colors.OUTLINE), border_radius=8
        )
        
        # 2. File List
        self.lbl_file_count = ft.Text("선택된 파일: 0 / 0개")
        self.file_list_view = ft.ListView(expand=True, spacing=2)
        
        btn_frame = ft.Column([
            ft.TextButton("전체 선택", on_click=self.select_all),
            ft.TextButton("선택 해제", on_click=self.deselect_all),
            ft.Divider(),
            ft.TextButton("▲ 위로 이동", on_click=self.move_up),
            ft.TextButton("▼ 아래로 이동", on_click=self.move_down),
            ft.Divider(),
            ft.TextButton("❌ 선택 제외", on_click=self.remove_from_list, style=ft.ButtonStyle(color=ft.colors.ERROR)),
        ])
        
        list_frame = ft.Container(
            content=ft.Column([
                ft.Text("이미지 파일 목록", weight=ft.FontWeight.BOLD),
                self.lbl_file_count,
                ft.Row([
                    ft.Container(content=self.file_list_view, expand=True, border=ft.border.all(1, ft.colors.OUTLINE), border_radius=5, padding=5),
                    btn_frame
                ], expand=True)
            ]),
            expand=True, padding=10, border=ft.border.all(1, ft.colors.OUTLINE), border_radius=8
        )
        
        # 3. Settings Tabs
        self.build_compress_tab()
        self.build_rename_tab()
        
        self.tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(text="압축 및 이름변경", content=self.tab_compress),
                ft.Tab(text="단순 이름변경", content=self.tab_rename)
            ],
            expand=True
        )
        
        settings_frame = ft.Container(
            content=self.tabs,
            height=280, padding=10, border=ft.border.all(1, ft.colors.OUTLINE), border_radius=8
        )
        
        # 4. Run Button
        self.btn_run = ft.ElevatedButton(
            "🚀 실행", 
            style=ft.ButtonStyle(bgcolor=ft.colors.PRIMARY, color=ft.colors.ON_PRIMARY, padding=ft.padding.all(20)),
            on_click=self.start_conversion
        )
        
        return ft.Column([
            folder_frame,
            list_frame,
            settings_frame,
            ft.Container(content=self.btn_run, alignment=ft.alignment.center)
        ], expand=True)
        
    def build_compress_tab(self):
        self.c_name_input = ft.TextField(label="변경할 이름 (영문)", value="my image", width=200, on_change=self.update_c_preview)
        self.c_sep_rg = ft.RadioGroup(content=ft.Row([ft.Radio(value="_", label="_ (언더바)"), ft.Radio(value="-", label="- (하이픈)")]), value="_", on_change=self.update_c_preview)
        self.c_preview_lbl = ft.Text("", color=ft.colors.BLUE, weight=ft.FontWeight.BOLD)
        
        self.c_save_loc = ft.RadioGroup(content=ft.Row([ft.Radio(value="same", label="현재 폴더"), ft.Radio(value="sub", label="하위 폴더")]), value="sub", on_change=self.toggle_c_subfolder)
        self.c_sub_name = ft.TextField(label="폴더명", value="output", width=120)
        self.c_date_prefix = ft.Dropdown(options=[ft.dropdown.Option("datetime", "년월일시"), ft.dropdown.Option("date", "년월일"), ft.dropdown.Option("none", "사용안함")], value="datetime", width=120)
        self.c_sub_row = ft.Row([self.c_sub_name, self.c_date_prefix])
        
        self.c_orig = ft.RadioGroup(content=ft.Row([ft.Radio(value="keep", label="유지"), ft.Radio(value="delete", label="삭제")]), value="keep")
        self.c_comp = ft.Dropdown(options=[ft.dropdown.Option("6", "최대(느림)"), ft.dropdown.Option("4", "일반(적정)"), ft.dropdown.Option("0", "빠름")], value="6", width=150, label="압축 강도", on_change=self.on_comp_change)
        self.c_preview_size = ft.Switch(label="예상 용량 계산 (느려짐)", value=False, on_change=self.on_comp_change)
        
        self.tab_compress = ft.Column([
            ft.Row([self.c_name_input, ft.Text("이름 연결 기호:"), self.c_sep_rg]),
            ft.Row([ft.Text("적용 예시:", color=ft.colors.BLUE), self.c_preview_lbl]),
            ft.Row([ft.Text("저장 위치:"), self.c_save_loc, self.c_sub_row]),
            ft.Row([ft.Text("원본 파일:"), self.c_orig, self.c_comp, self.c_preview_size])
        ], scroll=ft.ScrollMode.AUTO)
        self.update_c_preview(None)
        
    def build_rename_tab(self):
        self.r_name_input = ft.TextField(label="변경할 이름", value="사진 고양이", width=200, on_change=self.update_r_preview)
        self.r_sep_rg = ft.RadioGroup(content=ft.Row([ft.Radio(value="_", label="_ (언더바)"), ft.Radio(value="-", label="- (하이픈)")]), value="-", on_change=self.update_r_preview)
        self.r_preview_lbl = ft.Text("", color=ft.colors.BLUE, weight=ft.FontWeight.BOLD)
        
        self.r_pad = ft.Dropdown(options=[ft.dropdown.Option(x) for x in ["지정안함", "자동", "2자리", "3자리", "4자리", "5자리", "6자리"]], value="자동", width=120, label="숫자 패딩", on_change=self.update_r_preview)
        self.r_ext = ft.Dropdown(options=[ft.dropdown.Option(x) for x in ["원본 유지", ".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"]], value="원본 유지", width=120, label="확장자", on_change=self.update_r_preview)
        
        self.r_save_loc = ft.RadioGroup(content=ft.Row([ft.Radio(value="same", label="현재 폴더"), ft.Radio(value="sub", label="하위 폴더")]), value="sub", on_change=self.toggle_r_subfolder)
        self.r_sub_name = ft.TextField(label="폴더명", value="renamed", width=120)
        self.r_date_prefix = ft.Dropdown(options=[ft.dropdown.Option("datetime", "년월일시"), ft.dropdown.Option("date", "년월일"), ft.dropdown.Option("none", "사용안함")], value="none", width=120)
        self.r_sub_row = ft.Row([self.r_sub_name, self.r_date_prefix])
        
        self.r_orig = ft.RadioGroup(content=ft.Row([ft.Radio(value="keep", label="유지 (복사)"), ft.Radio(value="delete", label="삭제 (이동)")]), value="keep")
        
        self.tab_rename = ft.Column([
            ft.Row([self.r_name_input, ft.Text("이름 연결 기호:"), self.r_sep_rg]),
            ft.Row([self.r_pad, self.r_ext]),
            ft.Row([ft.Text("적용 예시:", color=ft.colors.BLUE), self.r_preview_lbl]),
            ft.Row([ft.Text("저장 위치:"), self.r_save_loc, self.r_sub_row]),
            ft.Row([ft.Text("원본 파일:"), self.r_orig])
        ], scroll=ft.ScrollMode.AUTO)
        self.update_r_preview(None)

    def on_comp_change(self, e):
        self.preview_size_val = self.c_preview_size.value
        self.compression_val = self.c_comp.value
        if self.selected_file_indices:
            self.trigger_selection_event()

    def update_c_preview(self, e):
        raw_name = self.c_name_input.value.strip()
        sep = self.c_sep_rg.value
        processed = raw_name.replace(" ", sep) if raw_name else "이름없음"
        self.c_preview_lbl.value = f"{processed}{sep}1.webp"
        self.page.update()
        
    def toggle_c_subfolder(self, e):
        self.c_sub_row.visible = (self.c_save_loc.value == "sub")
        self.page.update()
        
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
        self.page.update()
        
    def toggle_r_subfolder(self, e):
        self.r_sub_row.visible = (self.r_save_loc.value == "sub")
        self.page.update()

    def on_folder_selected(self, e):
        if e.path:
            folder = e.path
            self.app_state['selected_folder'] = folder
            self.lbl_folder_path.value = folder
            self.lbl_folder_path.color = ft.colors.ON_SURFACE
            
            self.app_state['image_files'] = []
            self.app_state['rotations'] = {}
            valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp')
            
            for f in os.listdir(folder):
                if f.lower().endswith(valid_extensions):
                    self.app_state['image_files'].append(f)
                    
            self.refresh_listbox()
            self.select_all(None)
            self.on_log(f"📁 폴더에서 {len(self.app_state['image_files'])}개의 이미지를 불러왔습니다.")

    def refresh_listbox(self):
        self.file_list_view.controls.clear()
        for i, f in enumerate(self.app_state['image_files']):
            is_selected = i in self.selected_file_indices
            
            def make_on_click(idx):
                return lambda e: self.toggle_selection(idx)
                
            container = ft.Container(
                content=ft.Text(f),
                padding=5,
                bgcolor=ft.colors.PRIMARY_CONTAINER if is_selected else ft.colors.TRANSPARENT,
                on_click=make_on_click(i)
            )
            self.file_list_view.controls.append(container)
        self.update_file_count()
        self.page.update()
        
    def toggle_selection(self, idx):
        if idx in self.selected_file_indices:
            self.selected_file_indices.remove(idx)
        else:
            self.selected_file_indices.add(idx)
        self.refresh_listbox()
        self.trigger_selection_event()
        
    def select_all(self, e):
        self.selected_file_indices = set(range(len(self.app_state['image_files'])))
        self.refresh_listbox()
        self.trigger_selection_event()
        
    def deselect_all(self, e):
        self.selected_file_indices.clear()
        self.refresh_listbox()
        self.trigger_selection_event()
        
    def update_file_count(self):
        total = len(self.app_state['image_files'])
        selected = len(self.selected_file_indices)
        self.lbl_file_count.value = f"선택된 파일: {selected} / {total}개"

    def trigger_selection_event(self):
        selected_files = [self.app_state['image_files'][i] for i in sorted(self.selected_file_indices)]
        self.on_selection_change(selected_files)

    def get_selected_files(self):
        return [self.app_state['image_files'][i] for i in sorted(self.selected_file_indices)]

    def move_up(self, e):
        if not self.selected_file_indices: return
        sorted_idx = sorted(list(self.selected_file_indices))
        new_selection = set()
        for i in sorted_idx:
            if i > 0 and (i-1) not in new_selection:
                self.app_state['image_files'][i], self.app_state['image_files'][i-1] = self.app_state['image_files'][i-1], self.app_state['image_files'][i]
                new_selection.add(i-1)
            else:
                new_selection.add(i)
        self.selected_file_indices = new_selection
        self.refresh_listbox()
        self.trigger_selection_event()

    def move_down(self, e):
        if not self.selected_file_indices: return
        sorted_idx = sorted(list(self.selected_file_indices), reverse=True)
        new_selection = set()
        max_idx = len(self.app_state['image_files']) - 1
        for i in sorted_idx:
            if i < max_idx and (i+1) not in new_selection:
                self.app_state['image_files'][i], self.app_state['image_files'][i+1] = self.app_state['image_files'][i+1], self.app_state['image_files'][i]
                new_selection.add(i+1)
            else:
                new_selection.add(i)
        self.selected_file_indices = new_selection
        self.refresh_listbox()
        self.trigger_selection_event()

    def remove_from_list(self, e):
        if not self.selected_file_indices: return
        sorted_idx = sorted(list(self.selected_file_indices), reverse=True)
        for i in sorted_idx:
            del self.app_state['image_files'][i]
        self.selected_file_indices.clear()
        self.refresh_listbox()
        self.trigger_selection_event()
        self.on_log(f"🗑️ 목록에서 {len(sorted_idx)}개의 파일이 제외되었습니다.")

    def handle_rotate(self):
        if not self.selected_file_indices: return
        first_idx = sorted(self.selected_file_indices)[0]
        filename = self.app_state['image_files'][first_idx]
        filepath = os.path.join(self.app_state['selected_folder'], filename)
        
        current_rot = self.app_state['rotations'].get(filepath, 0)
        self.app_state['rotations'][filepath] = (current_rot - 90) % 360
        self.on_file_rotated(filepath)

    def set_run_button_state(self, state):
        self.btn_run.disabled = not state
        self.page.update()

    def start_conversion(self, e):
        if not self.app_state.get('selected_folder'):
            return self.show_snack("먼저 폴더를 선택해주세요.")
            
        selected_files = self.get_selected_files()
        if not selected_files:
            return self.show_snack("처리할 이미지를 선택해주세요.")

        tab_idx = self.tabs.selected_index
        if tab_idx == 0:
            raw_name = self.c_name_input.value.strip()
            if not raw_name: return self.show_snack("변경할 영문 이름을 입력해주세요.")
            
            settings = {
                'mode': 'compress',
                'raw_name': raw_name,
                'separator': self.c_sep_rg.value,
                'save_location': self.c_save_loc.value,
                'subfolder_name': self.c_sub_name.value.strip(),
                'date_prefix': self.c_date_prefix.value,
                'delete_orig': self.c_orig.value == "delete",
                'compression_method': self.c_comp.value,
            }
            self.execute_run(selected_files, settings)
        else:
            raw_name = self.r_name_input.value.strip()
            if not raw_name: return self.show_snack("변경할 이름을 입력해주세요.")
            
            settings = {
                'mode': 'rename',
                'raw_name': raw_name,
                'separator': self.r_sep_rg.value,
                'save_location': self.r_save_loc.value,
                'subfolder_name': self.r_sub_name.value.strip(),
                'date_prefix': self.r_date_prefix.value,
                'delete_orig': self.r_orig.value == "delete",
                'pad_mode': self.r_pad.value,
                'target_ext': self.r_ext.value
            }
            
            base_name = raw_name.replace(" ", settings['separator'])
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
            self.page.overlay.append(dialog)
            dialog.open = True
            self.page.update()

    def show_snack(self, message):
        self.page.snack_bar = ft.SnackBar(ft.Text(message))
        self.page.snack_bar.open = True
        self.page.update()

    def execute_run(self, selected_files, settings):
        self.set_run_button_state(False)
        self.on_run(True)
        
        def log_cb(msg):
            self.on_log(msg)
            
        def progress_cb(current, total):
            self.page.pubsub.send_all(("progress", current, total)) # just direct call in flet isn't thread safe without page update, but page.update is fine if passed. We can pass direct callback.
            # actually we can just pass callback that does page.update
            # but wait, the callback is from another thread. In flet, UI updates from other threads should be safe if we call page.update()
            self.page.window_to_front() # optional
            
        callbacks = {
            'log': lambda m: self.page.run_thread(self.on_log, m),
            'progress': lambda c, t: self.page.run_thread(self.page.pubsub.send_all, ("progress", c, t)),
            'done': lambda s, e, b: self.page.run_thread(self.on_run_done)
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
        self.set_run_button_state(True)
        self.on_run(False)
