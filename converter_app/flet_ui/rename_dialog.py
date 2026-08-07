import flet as ft

class RenameDialog(ft.AlertDialog):
    def __init__(self, old_names, new_names, on_confirm):
        super().__init__()
        self.old_names = old_names
        self.new_names = new_names
        self.on_confirm = on_confirm
        
        self.title = ft.Text("이름 변경 미리보기")
        
        list_items = []
        for old, new in zip(old_names, new_names):
            list_items.append(ft.Text(f"{old}  ->  {new}", size=13))
            
        self.content = ft.Container(
            content=ft.ListView(controls=list_items, expand=True),
            width=500,
            height=300
        )
        
        self.actions = [
            ft.TextButton("취소", on_click=self.cancel),
            ft.ElevatedButton("변경 실행", on_click=self.confirm, bgcolor=ft.colors.BLUE, color=ft.colors.WHITE),
        ]
        
    def cancel(self, e):
        self.open = False
        self.page.update()
        
    def confirm(self, e):
        self.open = False
        self.page.update()
        self.on_confirm()
