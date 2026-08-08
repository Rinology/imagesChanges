import customtkinter as ctk

class RenameDialog(ctk.CTkToplevel):
    def __init__(self, master, original_names, new_names, on_confirm):
        super().__init__(master)
        self.title("이름 변경 확인")
        self.geometry("600x400")
        
        # Make the dialog modal
        self.transient(master)
        self.grab_set()
        
        self.update_idletasks()
        width = 600
        height = 400
        x = master.winfo_x() + (master.winfo_width() // 2) - (width // 2)
        y = master.winfo_y() + (master.winfo_height() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        
        self.on_confirm = on_confirm
        
        # Grid layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Main frame
        main_frame = ctk.CTkFrame(self)
        main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        lbl = ctk.CTkLabel(main_frame, text="다음과 같이 파일 이름이 변경됩니다. 진행하시겠습니까?", font=ctk.CTkFont(weight="bold"))
        lbl.grid(row=0, column=0, pady=(10, 10))
        
        # Scrollable textbox for list
        self.textbox = ctk.CTkTextbox(main_frame)
        self.textbox.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        # Populate textbox
        text_content = ""
        for orig, new in zip(original_names, new_names):
            text_content += f"{orig}  ➔  {new}\n"
            
        self.textbox.insert("0.0", text_content)
        self.textbox.configure(state="disabled")
        
        # Buttons
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.grid(row=2, column=0, pady=10)
        
        btn_cancel = ctk.CTkButton(btn_frame, text="취소", command=self.destroy, fg_color="gray", hover_color="#555555")
        btn_cancel.grid(row=0, column=0, padx=10)
        
        btn_ok = ctk.CTkButton(btn_frame, text="확인 및 진행", command=self.confirm_action)
        btn_ok.grid(row=0, column=1, padx=10)
        
    def confirm_action(self):
        self.on_confirm()
        self.destroy()
