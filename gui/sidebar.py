import customtkinter as ctk


class Sidebar(ctk.CTkFrame):

    def __init__(
        self,
        parent,
        new_chat_callback=None,
        action_callback=None,
        chat_open_callback=None,
        chat_delete_callback=None,
        settings_callback=None
    ):
        super().__init__(
            parent,
            width=250,
            corner_radius=18,
            fg_color="#0d1320",
            border_width=1,
            border_color="#1c2738"
        )

        self.pack_propagate(False)

        self.new_chat_callback = new_chat_callback
        self.action_callback = action_callback
        self.chat_open_callback = chat_open_callback
        self.chat_delete_callback = chat_delete_callback
        self.settings_callback = settings_callback

        self.chat_buttons = []

        # ==================================================
        # TOP
        # ==================================================

        top = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )
        top.pack(
            fill="x",
            padx=14,
            pady=(16, 8)
        )

        ctk.CTkLabel(
            top,
            text="Workspace",
            font=("Segoe UI", 15, "bold"),
            text_color="#d9e2ef"
        ).pack(
            anchor="w",
            pady=(0, 10)
        )

        self.new_chat_btn = ctk.CTkButton(
            top,
            text="+  New conversation",
            height=40,
            corner_radius=11,
            font=("Segoe UI", 12, "bold"),
            command=self.new_chat
        )
        self.new_chat_btn.pack(
            fill="x",
            pady=(0, 7)
        )

        # ALWAYS VISIBLE SETTINGS BUTTON
        self.settings_button = ctk.CTkButton(
            top,
            text="⚙  Settings",
            height=38,
            corner_radius=11,
            anchor="w",
            fg_color="#162235",
            hover_color="#21324d",
            text_color="#d7e1ee",
            font=("Segoe UI", 11, "bold"),
            command=self.open_settings
        )
        self.settings_button.pack(
            fill="x"
        )

        # ==================================================
        # RECENT CHATS
        # ==================================================

        ctk.CTkLabel(
            self,
            text="RECENT CHATS",
            font=("Segoe UI", 10, "bold"),
            text_color="#65758b"
        ).pack(
            anchor="w",
            padx=18,
            pady=(14, 7)
        )

        self.history_frame = ctk.CTkScrollableFrame(
            self,
            height=190,
            fg_color="transparent",
            scrollbar_button_color="#233047",
            scrollbar_button_hover_color="#33445e"
        )
        self.history_frame.pack(
            fill="x",
            padx=8
        )

        # ==================================================
        # QUICK ACTIONS
        # ==================================================

        ctk.CTkLabel(
            self,
            text="QUICK ACTIONS",
            font=("Segoe UI", 10, "bold"),
            text_color="#65758b"
        ).pack(
            anchor="w",
            padx=18,
            pady=(14, 7)
        )

        self.add_action(
            "◉  Analyze screen",
            "what's on my screen?"
        )

        self.add_action(
            "⚙  My routines",
            "show my routines"
        )

        self.add_action(
            "◫  My notes",
            "show my notes"
        )

        self.add_action(
            "⌁  My reminders",
            "show my reminders"
        )

        self.add_action(
            "◇  Memory",
            "what do you remember about me?"
        )

        spacer = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )
        spacer.pack(
            fill="both",
            expand=True
        )

    # ==================================================
    # CHAT HISTORY
    # ==================================================

    def load_chats(
        self,
        chats,
        active_chat_id=None
    ):
        for widget in self.history_frame.winfo_children():
            widget.destroy()

        self.chat_buttons.clear()

        if not chats:
            ctk.CTkLabel(
                self.history_frame,
                text="No conversations yet",
                font=("Segoe UI", 10),
                text_color="#65758b"
            ).pack(
                anchor="w",
                padx=8,
                pady=8
            )
            return

        for chat in chats:
            chat_id = chat.get("id")
            title = chat.get(
                "title",
                "New conversation"
            )

            row = ctk.CTkFrame(
                self.history_frame,
                fg_color=(
                    "#162235"
                    if chat_id == active_chat_id
                    else "transparent"
                ),
                corner_radius=9
            )
            row.pack(
                fill="x",
                pady=2
            )

            open_button = ctk.CTkButton(
                row,
                text=title,
                height=34,
                anchor="w",
                fg_color="transparent",
                hover_color="#1c2a40",
                text_color="#bdc8d8",
                font=("Segoe UI", 10),
                command=lambda cid=chat_id: self.open_chat(
                    cid
                )
            )
            open_button.pack(
                side="left",
                fill="x",
                expand=True,
                padx=(4, 0)
            )

            delete_button = ctk.CTkButton(
                row,
                text="×",
                width=28,
                height=28,
                corner_radius=8,
                fg_color="transparent",
                hover_color="#3a1d2b",
                text_color="#fb7185",
                font=("Segoe UI", 13, "bold"),
                command=lambda cid=chat_id: self.delete_chat(
                    cid
                )
            )
            delete_button.pack(
                side="right",
                padx=4
            )

            self.chat_buttons.append(row)

    def open_chat(self, chat_id):
        if self.chat_open_callback:
            self.chat_open_callback(
                chat_id
            )

    def delete_chat(self, chat_id):
        if self.chat_delete_callback:
            self.chat_delete_callback(
                chat_id
            )

    # ==================================================
    # QUICK ACTIONS
    # ==================================================

    def add_action(self, label, command):
        button = ctk.CTkButton(
            self,
            text=label,
            height=36,
            anchor="w",
            fg_color="transparent",
            hover_color="#162235",
            text_color="#bdc8d8",
            font=("Segoe UI", 11),
            command=lambda: self.run_action(
                command
            )
        )

        button.pack(
            fill="x",
            padx=12,
            pady=1
        )

    def run_action(self, command):
        if self.action_callback:
            self.action_callback(
                command
            )

    def new_chat(self):
        if self.new_chat_callback:
            self.new_chat_callback()

    def open_settings(self):
        if self.settings_callback:
            self.settings_callback()
