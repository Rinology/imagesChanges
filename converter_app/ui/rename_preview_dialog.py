import tkinter as tk
from tkinter import ttk

class RenamePreviewDialog(tk.Toplevel):
    def __init__(self, parent, original_names, new_names, on_confirm):
        super().__init__(parent)
        self.title("이름 변경 미리보기")
        self.geometry("600x400")
        self.transient(parent) # 부모 창 위에 띄우기
        self.grab_set() # 모달 창으로 만들기
        
        self.original_names = original_names
        self.new_names = new_names
        self.on_confirm = on_confirm
        
        self.setup_ui()
        
    def setup_ui(self):
        # 상단 안내 문구
        lbl_info = ttk.Label(self, text=f"총 {len(self.original_names)}개의 파일 이름이 아래와 같이 변경(복사/이동)됩니다.\n계속 진행하시겠습니까?", justify=tk.CENTER, font=("맑은 고딕", 10, "bold"))
        lbl_info.pack(pady=10)
        
        # 트리뷰(표) 영역
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        scroll_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree = ttk.Treeview(tree_frame, columns=("original", "new"), show="headings", yscrollcommand=scroll_y.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_y.config(command=self.tree.yview)
        
        self.tree.heading("original", text="변경 전 이름")
        self.tree.heading("new", text="변경 후 이름")
        self.tree.column("original", width=250, anchor=tk.W)
        self.tree.column("new", width=250, anchor=tk.W)
        
        # 데이터 삽입
        for orig, new in zip(self.original_names, self.new_names):
            self.tree.insert("", tk.END, values=(orig, new))
            
        # 하단 버튼 영역
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, pady=10)
        
        # 중앙 정렬을 위해 좌우 빈 프레임 추가
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(3, weight=1)
        
        btn_confirm = ttk.Button(btn_frame, text="✅ Okay (적용)", command=self.confirm)
        btn_confirm.grid(row=0, column=1, padx=5)
        
        btn_cancel = ttk.Button(btn_frame, text="❌ Cancel (취소)", command=self.cancel)
        btn_cancel.grid(row=0, column=2, padx=5)
        
    def confirm(self):
        self.on_confirm()
        self.destroy()
        
    def cancel(self):
        self.destroy()
