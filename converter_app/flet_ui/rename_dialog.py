import flet as ft

class RenameDialog(ft.AlertDialog):
    def __init__(self, old_names, new_names, on_confirm):
        super().__init__()
        self.old_names = old_names
        self.new_names = new_names
        self.on_confirm = on_confirm
        
        self.title = ft.Text("이름 변경 확인")
        
        list_view = ft.ListView(spacing=5, height=300, width=500)
        for old, new in zip(old_names, new_names):
            list_view.controls.append(ft.Text(f"{old} -> {new}", size=12))
            
        self.content = list_view
        
        self.actions = [
            ft.TextButton("취소", on_click=self.close_dialog),
            ft.TextButton("변경하기", on_click=self.confirm_dialog)
        ]
        
    def close_dialog(self, e):
        self.open = False
        if self.page:
            self.page.update()
            
    def confirm_dialog(self, e):
        self.open = False
        if self.page:
            self.page.update()
        self.on_confirm()
