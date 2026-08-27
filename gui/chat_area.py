import customtkinter as ctk


class ChatArea(ctk.CTkScrollableFrame):

    def __init__(self, parent):
        super().__init__(
            parent,
            fg_color="#090f1a",
            corner_radius=14,
            scrollbar_button_color="#233047",
            scrollbar_button_hover_color="#33445e"
        )

        self.messages = []
        self.message_data = []

        self.typing_widget = None
        self.listening_widget = None
        self.welcome_widget = None

        self.search_visible = False

        # ==================================================
        # SEARCH BAR
        # ==================================================

        self.search_row = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )
        self.search_row.pack(
            fill="x",
            padx=18,
            pady=(10, 2)
        )

        self.search_entry = ctk.CTkEntry(
            self.search_row,
            placeholder_text="Search this conversation...",
            height=34,
            corner_radius=10,
            fg_color="#0f1724",
            border_color="#233047",
            font=("Segoe UI", 11)
        )
        self.search_entry.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 7)
        )

        self.search_entry.bind(
            "<KeyRelease>",
            self._search_changed
        )

        self.search_clear = ctk.CTkButton(
            self.search_row,
            text="Clear",
            width=58,
            height=34,
            corner_radius=10,
            fg_color="#172338",
            hover_color="#21324d",
            font=("Segoe UI", 10),
            command=self.clear_search
        )
        self.search_clear.pack(
            side="left"
        )

    # ==================================================
    # WELCOME
    # ==================================================

    def show_welcome(self):
        if self.messages:
            return

        if (
            self.welcome_widget
            and self.welcome_widget.winfo_exists()
        ):
            return

        self.welcome_widget = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )
        self.welcome_widget.pack(
            fill="x",
            padx=28,
            pady=(55, 24)
        )

        ctk.CTkLabel(
            self.welcome_widget,
            text="J",
            width=58,
            height=58,
            corner_radius=18,
            fg_color="#2563eb",
            font=("Segoe UI", 27, "bold")
        ).pack(
            pady=(0, 14)
        )

        ctk.CTkLabel(
            self.welcome_widget,
            text="What can I help you with?",
            font=("Segoe UI", 24, "bold")
        ).pack()

        ctk.CTkLabel(
            self.welcome_widget,
            text=(
                "Ask a question, control your PC, use screen vision, "
                "or run one of your routines."
            ),
            text_color="#7f8da3",
            font=("Segoe UI", 12),
            wraplength=620
        ).pack(
            pady=(8, 0)
        )

    def _remove_welcome(self):
        if (
            self.welcome_widget
            and self.welcome_widget.winfo_exists()
        ):
            self.welcome_widget.destroy()

        self.welcome_widget = None

    # ==================================================
    # LOAD SAVED CHAT
    # ==================================================

    def load_messages(self, messages):
        self.clear()

        for item in messages:
            sender = item.get(
                "sender",
                "Jeroo"
            )

            message = item.get(
                "message",
                ""
            )

            self.add_message(
                sender,
                message
            )

        if not messages:
            self.show_welcome()

    # ==================================================
    # MESSAGE BUBBLES
    # ==================================================

    def add_message(self, sender, message):
        self._remove_welcome()

        row = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )
        row.pack(
            fill="x",
            padx=18,
            pady=6
        )

        is_user = sender.lower() == "you"

        bubble = ctk.CTkFrame(
            row,
            fg_color=(
                "#1d4ed8"
                if is_user
                else "#141d2b"
            ),
            corner_radius=16,
            border_width=(
                0
                if is_user
                else 1
            ),
            border_color="#223047"
        )

        bubble.pack(
            side=(
                "right"
                if is_user
                else "left"
            ),
            padx=(
                (90, 0)
                if is_user
                else (0, 90)
            )
        )

        name = ctk.CTkLabel(
            bubble,
            text=(
                "YOU"
                if is_user
                else "JEROO"
            ),
            font=("Segoe UI", 9, "bold"),
            text_color=(
                "#bfdbfe"
                if is_user
                else "#60a5fa"
            )
        )
        name.pack(
            anchor="w",
            padx=14,
            pady=(10, 2)
        )

        body = ctk.CTkLabel(
            bubble,
            text=str(message),
            wraplength=670,
            justify="left",
            anchor="w",
            font=("Segoe UI", 13),
            text_color="#edf3fb"
        )
        body.pack(
            anchor="w",
            padx=14,
            pady=(0, 11)
        )

        self.messages.append(row)
        self.message_data.append({
            "widget": row,
            "sender": str(sender),
            "message": str(message)
        })

        self._scroll_bottom()

    # ==================================================
    # SEARCH
    # ==================================================

    def _search_changed(self, event=None):
        query = self.search_entry.get().strip().lower()

        for item in self.message_data:
            widget = item["widget"]

            haystack = (
                item["sender"]
                + " "
                + item["message"]
            ).lower()

            if not query or query in haystack:
                if not widget.winfo_ismapped():
                    widget.pack(
                        fill="x",
                        padx=18,
                        pady=6
                    )
            else:
                widget.pack_forget()

        self._scroll_bottom()

    def clear_search(self):
        self.search_entry.delete(
            0,
            "end"
        )
        self._search_changed()

    # ==================================================
    # INDICATORS
    # ==================================================

    def _indicator(self, text):
        row = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )
        row.pack(
            fill="x",
            padx=18,
            pady=6
        )

        card = ctk.CTkFrame(
            row,
            fg_color="#141d2b",
            corner_radius=14,
            border_width=1,
            border_color="#223047"
        )
        card.pack(side="left")

        ctk.CTkLabel(
            card,
            text=text,
            font=("Segoe UI", 12),
            text_color="#9fb0c6"
        ).pack(
            padx=14,
            pady=10
        )

        self._scroll_bottom()

        return row

    def add_typing_indicator(self):
        self.remove_typing_indicator()

        self.typing_widget = self._indicator(
            "Jeroo is thinking  •  •  •"
        )

    def remove_typing_indicator(self):
        if (
            self.typing_widget
            and self.typing_widget.winfo_exists()
        ):
            self.typing_widget.destroy()

        self.typing_widget = None

    def add_listening_indicator(self):
        self.remove_listening_indicator()

        self.listening_widget = self._indicator(
            "Listening for your voice..."
        )

    def remove_listening_indicator(self):
        if (
            self.listening_widget
            and self.listening_widget.winfo_exists()
        ):
            self.listening_widget.destroy()

        self.listening_widget = None

    # Backward compatibility
    def remove_last_message(self):
        if self.messages:
            widget = self.messages.pop()

            if widget.winfo_exists():
                widget.destroy()

            for index in range(
                len(self.message_data) - 1,
                -1,
                -1
            ):
                if (
                    self.message_data[index]["widget"]
                    == widget
                ):
                    self.message_data.pop(index)
                    break

    # ==================================================
    # CLEAR
    # ==================================================

    def clear(self):
        self.remove_typing_indicator()
        self.remove_listening_indicator()

        for widget in self.messages:
            if widget.winfo_exists():
                widget.destroy()

        self.messages.clear()
        self.message_data.clear()

        self.clear_search()

        if (
            self.welcome_widget
            and self.welcome_widget.winfo_exists()
        ):
            self.welcome_widget.destroy()

        self.welcome_widget = None

    # ==================================================
    # SCROLL
    # ==================================================

    def _scroll_bottom(self):
        def scroll():
            try:
                self._parent_canvas.yview_moveto(
                    1.0
                )
            except Exception:
                pass

        try:
            self.after(
                30,
                scroll
            )
        except Exception:
            pass
