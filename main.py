import customtkinter as ctk
from converter_app.ctk_ui.main_window import MainWindow

def main():
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    
    app = ctk.CTk()
    app.title("Image Converter")
    app.geometry("1400x950")
    
    # Grid configure to make main_window fill the entire app
    app.grid_rowconfigure(0, weight=1)
    app.grid_columnconfigure(0, weight=1)
    
    main_window = MainWindow(app)
    main_window.grid(row=0, column=0, sticky="nsew")
    
    app.mainloop()

if __name__ == "__main__":
    main()
