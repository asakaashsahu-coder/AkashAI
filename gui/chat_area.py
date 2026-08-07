import customtkinter as ctk


class ChatArea(ctk.CTkScrollableFrame):

    def __init__(self, parent):

        super().__init__(parent)

        self.messages = []

    def add_message(self, sender, message):

        if sender.lower() == "you":

            color = "#2563eb"
            anchor = "e"

        else:

            color = "#2d2d2d"
            anchor = "w"

        bubble = ctk.CTkFrame(
            self,
            fg_color=color,
            corner_radius=15
        )

        bubble.pack(
            fill="x",
            padx=15,
            pady=8,
            anchor=anchor
        )

        sender_label = ctk.CTkLabel(
            bubble,
            text=sender,
            font=("Segoe UI", 12, "bold")
        )

        sender_label.pack(
            anchor="w",
            padx=12,
            pady=(8, 0)
        )

        message_label = ctk.CTkLabel(
            bubble,
            text=message,
            wraplength=700,
            justify="left",
            font=("Segoe UI", 14)
        )

        message_label.pack(
            anchor="w",
            padx=12,
            pady=(2, 10)
        )

        self.messages.append(
            bubble
        )

    def remove_last_message(self):

        if self.messages:

            widget = self.messages.pop()

            widget.destroy()

    def clear(self):

        for widget in self.messages:

            widget.destroy()

        self.messages.clear()