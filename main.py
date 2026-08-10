import customtkinter as ctk
from converter_app.ctk_ui.main_window import MainWindow

def main():
    """
    프로그램의 메인 진입점 함수입니다.
    - 테마와 기본 색상을 설정합니다.
    - 메인 윈도우(CTk)를 생성하고 해상도를 설정합니다.
    - MainWindow 컴포넌트를 초기화하여 화면에 배치합니다.
    - 메인 이벤트 루프를 시작합니다.
    """
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    ctk.set_widget_scaling(0.85)  # 글씨 및 위젯 크기 약간 축소
    ctk.set_window_scaling(0.85)
    
    app = ctk.CTk()
    app.title("Image Converter")
    app.geometry("1600x900")
    app.minsize(900, 700)
    
    # Grid configure to make main_window fill the entire app
    app.grid_rowconfigure(0, weight=1)
    app.grid_columnconfigure(0, weight=1)
    
    main_window = MainWindow(app)
    main_window.grid(row=0, column=0, sticky="nsew")
    
    app.mainloop()

import multiprocessing

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
