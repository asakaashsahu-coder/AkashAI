import customtkinter as ctk


class Sidebar(ctk.CTkFrame):

    def __init__(self, parent):
        super().__init__(parent, width=220, corner_radius=0)

        self.pack_propagate(False)

        title = ctk.CTkLabel(
            self,
            text="Chats",
            font=("Segoe UI", 20, "bold")
        )
        title.pack(pady=(20, 10))

        self.new_chat_btn = ctk.CTkButton(
            self,
            text="+ New Chat",
            height=40
        )
        self.new_chat_btn.pack(fill="x", padx=15, pady=10)

        self.chat_list = ctk.CTkScrollableFrame(
            self,
            width=180
        )
        self.chat_list.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )