import customtkinter as ctk


class Header(ctk.CTkFrame):

    def __init__(self, parent):
        super().__init__(
            parent,
            height=74,
            corner_radius=18,
            fg_color="#0d1320",
            border_width=1,
            border_color="#1c2738"
        )

        self.pack_propagate(False)

        self.current_status = "Starting"
        self.current_color = "#f59e0b"
        self.pulse_big = False

        # ==================================================
        # BRAND
        # ==================================================

        brand = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )
        brand.pack(
            side="left",
            padx=20,
            pady=11
        )

        self.logo = ctk.CTkLabel(
            brand,
            text="J",
            width=42,
            height=42,
            corner_radius=13,
            fg_color="#2563eb",
            font=("Segoe UI", 20, "bold")
        )
        self.logo.pack(side="left")

        title_block = ctk.CTkFrame(
            brand,
            fg_color="transparent"
        )
        title_block.pack(
            side="left",
            padx=(12, 0)
        )

        self.title_label = ctk.CTkLabel(
            title_block,
            text="Jeroo AI",
            font=("Segoe UI", 21, "bold"),
            anchor="w"
        )
        self.title_label.pack(anchor="w")

        self.subtitle_label = ctk.CTkLabel(
            title_block,
            text="Desktop assistant",
            font=("Segoe UI", 11),
            text_color="#7f8da3",
            anchor="w"
        )
        self.subtitle_label.pack(anchor="w")

        # ==================================================
        # SHORTCUT + STATUS
        # ==================================================

        right = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )
        right.pack(
            side="right",
            padx=18
        )

        shortcut = ctk.CTkLabel(
            right,
            text="Ctrl + Shift + J",
            font=("Segoe UI", 11),
            text_color="#7f8da3",
            fg_color="#111a2a",
            corner_radius=9,
            padx=10,
            pady=5
        )
        shortcut.pack(
            side="left",
            padx=(0, 10)
        )

        self.status_frame = ctk.CTkFrame(
            right,
            fg_color="#111a2a",
            corner_radius=12
        )
        self.status_frame.pack(side="left")

        self.status_dot = ctk.CTkLabel(
            self.status_frame,
            text="●",
            width=20,
            text_color=self.current_color,
            font=("Segoe UI", 13)
        )
        self.status_dot.pack(
            side="left",
            padx=(8, 0),
            pady=7
        )

        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Starting",
            font=("Segoe UI", 12, "bold"),
            text_color="#d9e2ef"
        )
        self.status_label.pack(
            side="left",
            padx=(2, 10),
            pady=7
        )

        self.after(
            450,
            self._pulse_status
        )

    # ==================================================
    # STATUS
    # ==================================================

    def set_status(self, status, color=None):
        display_names = {
            "starting": "Starting",
            "ready": "Ready",
            "wake listening": "Wake listening",
            "wake_listening": "Wake listening",
            "listening": "Listening",
            "thinking": "Thinking",
            "speaking": "Speaking",
            "error": "Error"
        }

        display = display_names.get(
            str(status).lower(),
            str(status)
        )

        self.current_status = display

        if color:
            self.current_color = color

        self.status_label.configure(
            text=display
        )

        self.status_dot.configure(
            text_color=self.current_color
        )

    # ==================================================
    # STATUS PULSE
    # ==================================================

    def _pulse_status(self):
        try:
            active_states = {
                "Starting",
                "Wake listening",
                "Listening",
                "Thinking",
                "Speaking"
            }

            if self.current_status in active_states:
                self.pulse_big = not self.pulse_big

                self.status_dot.configure(
                    font=(
                        "Segoe UI",
                        15 if self.pulse_big else 11
                    )
                )
            else:
                self.status_dot.configure(
                    font=("Segoe UI", 13)
                )

            self.after(
                450,
                self._pulse_status
            )

        except Exception:
            pass
