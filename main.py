import tkinter as tk
from converter_app.ui.main_window import ImageConverterApp

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageConverterApp(root)
    root.mainloop()
