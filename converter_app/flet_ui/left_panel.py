import flet as ft
import os
import base64
from converter_app.core.image_processor import ImageProcessor

class LeftPanel(ft.Container):
    def __init__(self, page, app_state, main_window):
        super().__init__(expand=True)
        self.app_page = page
        self.app_state = app_state
        self.main_window = main_window
        self.selected_file_indices = set()
        
        self.folder_picker = ft.FilePicker()
        self.app_page.overlay.append(self.folder_picker)
        
        self.content = self.build_ui()
        self.current_preview_file = None

    def build_ui(self):
        # 1. Folder Selection & File List (Top Left)
        self.lbl_folder_path = ft.Text("선택된 폴더 없음", color=ft.Colors.ON_SURFACE_VARIANT, expand=True)
        
        async def on_open_folder(e):
            path = await self.folder_picker.get_directory_path("이미지가 있는 폴더를 선택하세요")
            if path:
                self.on_folder_selected(path)
            
        folder_frame = ft.Container(
            content=ft.Row([
                ft.ElevatedButton("폴더 열기", icon=ft.Icons.FOLDER_OPEN, on_click=on_open_folder),
                self.lbl_folder_path
            ]),
            padding=10, border=ft.Border.all(1, ft.Colors.OUTLINE), border_radius=8
        )
        
        self.lbl_file_count = ft.Text("선택된 파일: 0 / 0개")
        self.file_list_view = ft.ListView(expand=True, spacing=2)
        
        btn_frame = ft.Column([
            ft.TextButton("전체 선택", on_click=self.select_all),
            ft.TextButton("선택 해제", on_click=self.deselect_all),
            ft.Divider(),
            ft.TextButton("▲ 위로 이동", on_click=self.move_up),
            ft.TextButton("▼ 아래로 이동", on_click=self.move_down),
            ft.Divider(),
            ft.TextButton("❌ 선택 제외", on_click=self.remove_from_list, style=ft.ButtonStyle(color=ft.Colors.ERROR)),
        ])
        
        list_frame = ft.Container(
            content=ft.Column([
                ft.Text("이미지 파일 목록", weight=ft.FontWeight.BOLD),
                self.lbl_file_count,
                ft.Row([
                    ft.Container(content=self.file_list_view, expand=True, border=ft.Border.all(1, ft.Colors.OUTLINE), border_radius=5, padding=5),
                    btn_frame
                ], expand=True)
            ]),
            expand=True, padding=10, border=ft.Border.all(1, ft.Colors.OUTLINE), border_radius=8
        )
        
        # 2. Image Preview (Bottom Left)
        transparent_1x1_bytes = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=")
        self.img_preview = ft.Image(
            src=transparent_1x1_bytes,
            fit=ft.BoxFit.CONTAIN,
            expand=True,
            tooltip="선택된 이미지 미리보기",
            error_content=ft.Text("이미지 없음", color=ft.Colors.ON_SURFACE_VARIANT)
        )
        self.lbl_info = ft.Text("선택된 이미지 없음", expand=True)
        self.btn_rotate = ft.IconButton(
            icon=ft.Icons.ROTATE_RIGHT,
            tooltip="90도 회전",
            on_click=self.handle_rotate,
            disabled=True
        )
        
        preview_frame = ft.Container(
            content=ft.Column([
                ft.Text("이미지 미리보기", weight=ft.FontWeight.BOLD),
                ft.Container(content=self.img_preview, expand=True, alignment=ft.Alignment.CENTER, bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST, border_radius=8),
                ft.Row([self.lbl_info, self.btn_rotate], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            ]),
            expand=True, border=ft.Border.all(1, ft.Colors.OUTLINE), border_radius=8, padding=10
        )
        
        return ft.Column([
            ft.Container(content=ft.Column([folder_frame, list_frame]), expand=True),
            preview_frame
        ], expand=True)
        
    def on_folder_selected(self, path):
        if path:
            self.app_state['selected_folder'] = path
            self.lbl_folder_path.value = path
            self.lbl_folder_path.color = ft.Colors.ON_SURFACE
            
            self.app_state['image_files'] = []
            self.app_state['rotations'] = {}
            valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp')
            
            for f in os.listdir(path):
                if f.lower().endswith(valid_extensions):
                    self.app_state['image_files'].append(f)
                    
            self.refresh_listbox()
            self.select_all(None)
            self.main_window.log(f"📁 폴더에서 {len(self.app_state['image_files'])}개의 이미지를 불러왔습니다.")

    def refresh_listbox(self):
        self.file_list_view.controls.clear()
        for i, f in enumerate(self.app_state['image_files']):
            is_selected = i in self.selected_file_indices
            def make_on_click(idx):
                return lambda e: self.toggle_selection(idx)
            container = ft.Container(
                content=ft.Text(f),
                padding=5,
                bgcolor=ft.Colors.PRIMARY_CONTAINER if is_selected else ft.Colors.TRANSPARENT,
                on_click=make_on_click(i)
            )
            self.file_list_view.controls.append(container)
        self.update_file_count()
        self.app_page.update()
        
    def toggle_selection(self, idx):
        if idx in self.selected_file_indices:
            self.selected_file_indices.remove(idx)
        else:
            self.selected_file_indices.add(idx)
        self.refresh_listbox()
        self.main_window.on_selection_change()
        
    def select_all(self, e):
        self.selected_file_indices = set(range(len(self.app_state['image_files'])))
        self.refresh_listbox()
        self.main_window.on_selection_change()
        
    def deselect_all(self, e):
        self.selected_file_indices.clear()
        self.refresh_listbox()
        self.main_window.on_selection_change()
        
    def update_file_count(self):
        total = len(self.app_state['image_files'])
        selected = len(self.selected_file_indices)
        self.lbl_file_count.value = f"선택된 파일: {selected} / {total}개"

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
        self.main_window.on_selection_change()

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
        self.main_window.on_selection_change()

    def remove_from_list(self, e):
        if not self.selected_file_indices: return
        sorted_idx = sorted(list(self.selected_file_indices), reverse=True)
        for i in sorted_idx:
            del self.app_state['image_files'][i]
        self.selected_file_indices.clear()
        self.refresh_listbox()
        self.main_window.on_selection_change()
        self.main_window.log(f"🗑️ 목록에서 {len(sorted_idx)}개의 파일이 제외되었습니다.")

    def handle_rotate(self, e):
        if not self.selected_file_indices: return
        first_idx = sorted(self.selected_file_indices)[0]
        filename = self.app_state['image_files'][first_idx]
        filepath = os.path.join(self.app_state['selected_folder'], filename)
        
        current_rot = self.app_state['rotations'].get(filepath, 0)
        self.app_state['rotations'][filepath] = (current_rot - 90) % 360
        self.update_preview()
        
    def update_preview(self):
        selected_files = self.get_selected_files()
        if not selected_files:
            self.img_preview.src_base64 = None
            self.lbl_info.value = "선택된 이미지 없음"
            self.btn_rotate.disabled = True
            self.current_preview_file = None
            self.app_page.update()
            return

        first_file = selected_files[0]
        filepath = os.path.join(self.app_state['selected_folder'], first_file)
        self.current_preview_file = filepath

        try:
            rot = self.app_state['rotations'].get(filepath, 0)
            b64_img = ImageProcessor.create_thumbnail(filepath, rot)
            self.img_preview.src = base64.b64decode(b64_img)
            self.btn_rotate.disabled = False
            
            orig_size = os.path.getsize(filepath)
            size_str = ImageProcessor.format_size(orig_size)
            
            comp_settings = self.main_window.get_compression_settings()
            preview_size_val = comp_settings.get('preview_size_val', False) if comp_settings else False
            compression_val = comp_settings.get('compression_method', '6') if comp_settings else '6'
            
            if not preview_size_val or self.main_window.get_current_mode() != 'compress':
                self.lbl_info.value = f"{first_file} ({size_str})"
                self.app_page.update()
            else:
                self.lbl_info.value = f"{first_file} ({size_str}) -> 예상 용량 계산 중..."
                self.app_page.update()
                
                def on_success(expected):
                    if self.current_preview_file == filepath:
                        self.lbl_info.value = f"{first_file} ({size_str}) -> 약 {ImageProcessor.format_size(expected)}"
                        self.app_page.update()
                def on_error(err):
                    if self.current_preview_file == filepath:
                        self.lbl_info.value = f"{first_file} ({size_str}) -> 계산 실패"
                        self.app_page.update()
                        
                ImageProcessor.calculate_expected_size_async(filepath, rot, compression_val, on_success, on_error)
                
        except Exception as e:
            self.img_preview.src_base64 = None
            self.lbl_info.value = f"{first_file} (미리보기 실패)"
            self.btn_rotate.disabled = True
            self.app_page.update()
