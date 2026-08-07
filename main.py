import tkinter as tk
import sv_ttk
from converter_app.ui.main_window import ImageConverterApp

# High-DPI awareness for Windows
try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageConverterApp(root)
    # 기본 테마를 다크 모드로 설정
    sv_ttk.set_theme("dark")
    root.mainloop()
