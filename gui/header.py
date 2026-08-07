import customtkinter as ctk


class Header(ctk.CTkFrame):

    def __init__(self, parent):
        super().__init__(parent, height=60, corner_radius=0)

        self.pack_propagate(False)

        self.title = ctk.CTkLabel(
            self,
            text="🤖 Jeroo",
            font=("Segoe UI", 24, "bold")
        )

        self.title.pack(side="left", padx=20, pady=15)

        self.status = ctk.CTkLabel(
            self,
            text="● Online",
            text_color="lightgreen",
            font=("Segoe UI", 14)
        )

        self.status.pack(side="right", padx=20)