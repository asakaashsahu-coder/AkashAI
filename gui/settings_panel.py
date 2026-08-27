import customtkinter as ctk


class SettingsPanel(ctk.CTkToplevel):

    def __init__(
        self,
        parent,
        settings_manager,
        on_apply=None,
        on_clear_history=None,
        on_clear_memory=None
    ):
        super().__init__(parent)

        self.settings_manager = settings_manager
        self.on_apply = on_apply
        self.on_clear_history = on_clear_history
        self.on_clear_memory = on_clear_memory

        self.title("Jeroo Settings")
        self.geometry("560x650")
        self.minsize(520, 600)

        self.configure(
            fg_color="#090d16"
        )

        self.transient(parent)

        self.grid_columnconfigure(
            0,
            weight=1
        )

        settings = self.settings_manager.get_all()

        # ==================================================
        # HEADER
        # ==================================================

        header = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )
        header.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=24,
            pady=(22, 12)
        )

        ctk.CTkLabel(
            header,
            text="Settings",
            font=("Segoe UI", 24, "bold")
        ).pack(anchor="w")

        ctk.CTkLabel(
            header,
            text="Personalize Jeroo without editing code.",
            font=("Segoe UI", 11),
            text_color="#7f8da3"
        ).pack(
            anchor="w",
            pady=(4, 0)
        )

        # ==================================================
        # PREFERENCES
        # ==================================================

        card = ctk.CTkFrame(
            self,
            fg_color="#0d1320",
            corner_radius=16,
            border_width=1,
            border_color="#1c2738"
        )
        card.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=24,
            pady=8
        )

        self._label(
            card,
            "Appearance"
        )

        self.appearance = ctk.CTkOptionMenu(
            card,
            values=["Dark", "System"]
        )
        self.appearance.set(
            settings.get(
                "appearance",
                "Dark"
            )
        )
        self.appearance.pack(
            fill="x",
            padx=16,
            pady=(0, 10)
        )

        self._label(
            card,
            "UI scale"
        )

        self.scale = ctk.CTkOptionMenu(
            card,
            values=["90%", "100%", "110%"]
        )
        self.scale.set(
            settings.get(
                "ui_scale",
                "100%"
            )
        )
        self.scale.pack(
            fill="x",
            padx=16,
            pady=(0, 10)
        )

        self._label(
            card,
            "Default browser"
        )

        self.browser = ctk.CTkOptionMenu(
            card,
            values=[
                "Chrome",
                "Edge"
            ]
        )
        self.browser.set(
            settings.get(
                "default_browser",
                "Chrome"
            )
        )
        self.browser.pack(
            fill="x",
            padx=16,
            pady=(0, 12)
        )

        self.voice_switch = ctk.CTkSwitch(
            card,
            text="Voice responses",
            font=("Segoe UI", 11)
        )
        self.voice_switch.pack(
            anchor="w",
            padx=16,
            pady=(4, 8)
        )

        if settings.get(
            "voice_enabled",
            True
        ):
            self.voice_switch.select()

        self.wake_switch = ctk.CTkSwitch(
            card,
            text="Enable Wake phrase on startup",
            font=("Segoe UI", 11)
        )
        self.wake_switch.pack(
            anchor="w",
            padx=16,
            pady=(0, 16)
        )

        if settings.get(
            "wake_phrase_enabled",
            False
        ):
            self.wake_switch.select()

        # ==================================================
        # DATA
        # ==================================================

        data_card = ctk.CTkFrame(
            self,
            fg_color="#0d1320",
            corner_radius=16,
            border_width=1,
            border_color="#1c2738"
        )
        data_card.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=24,
            pady=8
        )

        ctk.CTkLabel(
            data_card,
            text="Jeroo data",
            font=("Segoe UI", 13, "bold")
        ).pack(
            anchor="w",
            padx=16,
            pady=(14, 8)
        )

        button_row = ctk.CTkFrame(
            data_card,
            fg_color="transparent"
        )
        button_row.pack(
            fill="x",
            padx=12,
            pady=(0, 8)
        )

        ctk.CTkButton(
            button_row,
            text="Export backup",
            command=self.export_backup
        ).pack(
            side="left",
            fill="x",
            expand=True,
            padx=4
        )

        ctk.CTkButton(
            button_row,
            text="Clear chats",
            fg_color="#44202b",
            hover_color="#5a2837",
            command=self.clear_history
        ).pack(
            side="left",
            fill="x",
            expand=True,
            padx=4
        )

        ctk.CTkButton(
            data_card,
            text="Clear long-term memory",
            fg_color="#44202b",
            hover_color="#5a2837",
            command=self.clear_memory
        ).pack(
            fill="x",
            padx=16,
            pady=(0, 12)
        )

        self.info_label = ctk.CTkLabel(
            data_card,
            text="",
            wraplength=460,
            justify="left",
            font=("Segoe UI", 10),
            text_color="#8fa0b6"
        )
        self.info_label.pack(
            anchor="w",
            padx=16,
            pady=(0, 12)
        )

        # ==================================================
        # APPLY
        # ==================================================

        footer = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )
        footer.grid(
            row=3,
            column=0,
            sticky="ew",
            padx=24,
            pady=(10, 22)
        )

        ctk.CTkButton(
            footer,
            text="Save settings",
            height=42,
            font=("Segoe UI", 12, "bold"),
            command=self.save_settings
        ).pack(
            side="right"
        )

    def _label(
        self,
        parent,
        text
    ):
        ctk.CTkLabel(
            parent,
            text=text,
            font=("Segoe UI", 10),
            text_color="#8fa0b6"
        ).pack(
            anchor="w",
            padx=16,
            pady=(12, 4)
        )

    def save_settings(self):
        values = {
            "appearance": self.appearance.get(),
            "ui_scale": self.scale.get(),
            "default_browser": self.browser.get(),
            "voice_enabled": bool(
                self.voice_switch.get()
            ),
            "wake_phrase_enabled": bool(
                self.wake_switch.get()
            )
        }

        for key, value in values.items():
            self.settings_manager.set(
                key,
                value
            )

        if self.on_apply:
            self.on_apply(values)

        self.info_label.configure(
            text="✓ Settings saved."
        )

    def export_backup(self):
        path, copied = (
            self.settings_manager.export_data()
        )

        self.info_label.configure(
            text=(
                "Backup created in:\n"
                + path
                + "\nFiles: "
                + (
                    ", ".join(copied)
                    if copied
                    else "No data files yet"
                )
            )
        )

    def clear_history(self):
        if self.on_clear_history:
            self.on_clear_history()

        self.info_label.configure(
            text="Chat history cleared."
        )

    def clear_memory(self):
        if self.on_clear_memory:
            result = self.on_clear_memory()
        else:
            result = False

        if result:
            text = "Long-term memory cleared."
        else:
            text = (
                "No supported local memory file was found. "
                "Use Jerro's existing 'clear memory' command instead."
            )

        self.info_label.configure(
            text=text
        )
