import flet as ft
from converter_app.core.image_processor import ImageProcessor
import os

class RightPanel(ft.Container):
    def __init__(self, page, app_state, on_rotate_request):
        super().__init__(expand=True)
        self.app_page = page
        self.app_state = app_state
        self.on_rotate_request = on_rotate_request
        self.current_preview_file = None
        self.content = self.build_ui()

    def build_ui(self):
        self.img_preview = ft.Image(
            src="",
            fit=ft.BoxFit.CONTAIN,
            expand=True,
            tooltip="선택된 이미지 미리보기",
            error_content=ft.Text("이미지 없음", color=ft.Colors.ON_SURFACE_VARIANT)
        )
        self.lbl_info = ft.Text("", expand=True)
        self.btn_rotate = ft.IconButton(
            icon=ft.Icons.ROTATE_RIGHT,
            tooltip="90도 회전",
            on_click=lambda e: self.on_rotate_request(),
            disabled=True
        )

        self.progress_bar = ft.ProgressBar(value=0, visible=False)
        self.lbl_progress = ft.Text("대기 중...")
        self.log_list = ft.ListView(expand=True, spacing=5, auto_scroll=True)

        return ft.Column([
            ft.Container(
                content=ft.Column([
                    ft.Container(content=self.img_preview, expand=True, alignment=ft.Alignment.CENTER, bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST, border_radius=8),
                    ft.Row([self.lbl_info, self.btn_rotate], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                ]),
                expand=True,
                border=ft.Border.all(1, ft.Colors.OUTLINE),
                border_radius=8,
                padding=10
            ),
            ft.Container(
                content=ft.Column([
                    ft.Text("진행 상태 및 로그", weight=ft.FontWeight.BOLD),
                    self.progress_bar,
                    self.lbl_progress,
                    ft.Container(content=self.log_list, expand=True, bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST, border_radius=5, padding=5)
                ]),
                expand=True,
                border=ft.Border.all(1, ft.Colors.OUTLINE),
                border_radius=8,
                padding=10
            )
        ], expand=True)

    def log(self, message):
        self.log_list.controls.append(ft.Text(message, size=12, selectable=True))
        self.app_page.update()

    def update_selection(self, selected_files, preview_size_val, compression_val):
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
            self.img_preview.src_base64 = b64_img
            self.btn_rotate.disabled = False
            
            orig_size = os.path.getsize(filepath)
            size_str = ImageProcessor.format_size(orig_size)
            
            if not preview_size_val:
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

    def update_selection_after_rotate(self):
        if self.current_preview_file:
            first_file = os.path.basename(self.current_preview_file)
            self.update_selection([first_file], False, "4")

    def reset_progress(self):
        self.progress_bar.value = 0
        self.progress_bar.visible = True
        self.lbl_progress.value = "진행 중..."
        self.app_page.update()

    def update_progress(self, current, total):
        progress = (current / total) if total > 0 else 0
        self.progress_bar.value = progress
        self.lbl_progress.value = f"진행 상태: {current} / {total} 완료"
        self.app_page.update()
