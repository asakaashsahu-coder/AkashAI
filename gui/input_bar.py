import customtkinter as ctk


class InputBar(ctk.CTkFrame):

    def __init__(
        self,
        parent,
        send_callback,
        voice_callback=None,
        clear_callback=None,
        stop_callback=None,
        wake_callback=None,
        voice_chat_callback=None
    ):
        super().__init__(
            parent,
            fg_color="#101827",
            corner_radius=16,
            border_width=1,
            border_color="#1f2c40"
        )

        self.send_callback = send_callback
        self.voice_callback = voice_callback
        self.clear_callback = clear_callback
        self.stop_callback = stop_callback
        self.wake_callback = wake_callback
        self.voice_chat_callback = voice_chat_callback

        # ==================================================
        # TOP TOOL ROW
        # ==================================================

        tools = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )
        tools.pack(
            fill="x",
            padx=12,
            pady=(10, 4)
        )

        self.wake_switch = ctk.CTkSwitch(
            tools,
            text="Wake phrase",
            width=105,
            font=(
                "Segoe UI",
                11
            ),
            command=self.toggle_wake
        )
        self.wake_switch.pack(
            side="left"
        )

        self.voice_chat_switch = ctk.CTkSwitch(
            tools,
            text="Voice Chat",
            width=100,
            font=(
                "Segoe UI",
                11
            ),
            command=self.toggle_voice_chat
        )
        self.voice_chat_switch.pack(
            side="left",
            padx=(12, 0)
        )

        self.state_label = ctk.CTkLabel(
            tools,
            text="Ready",
            font=(
                "Segoe UI",
                10
            ),
            text_color="#6f8098"
        )
        self.state_label.pack(
            side="left",
            padx=12
        )

        self.clear_button = ctk.CTkButton(
            tools,
            text="Clear chat",
            width=76,
            height=27,
            corner_radius=9,
            fg_color="transparent",
            hover_color="#1a2639",
            text_color="#8292a8",
            font=(
                "Segoe UI",
                10
            ),
            command=self.clear_chat
        )
        self.clear_button.pack(
            side="right"
        )

        # ==================================================
        # COMPOSER
        # ==================================================

        composer = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )
        composer.pack(
            fill="x",
            padx=10,
            pady=(3, 10)
        )

        self.entry = ctk.CTkEntry(
            composer,
            placeholder_text=(
                "Message Jeroo or type a PC command..."
            ),
            height=46,
            corner_radius=13,
            fg_color="#0b111d",
            border_color="#26364e",
            border_width=1,
            font=(
                "Segoe UI",
                12
            )
        )
        self.entry.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 7)
        )

        self.entry.bind(
            "<Return>",
            self.send
        )

        self.mic_button = ctk.CTkButton(
            composer,
            text="🎤",
            width=46,
            height=46,
            corner_radius=13,
            fg_color="#172338",
            hover_color="#21324d",
            command=self.voice_input
        )
        self.mic_button.pack(
            side="left",
            padx=(0, 7)
        )

        self.stop_button = ctk.CTkButton(
            composer,
            text="■",
            width=46,
            height=46,
            corner_radius=13,
            fg_color="#331b27",
            hover_color="#4a2534",
            text_color="#fb7185",
            command=self.stop_speaking
        )
        self.stop_button.pack(
            side="left",
            padx=(0, 7)
        )

        self.send_button = ctk.CTkButton(
            composer,
            text="Send  ➜",
            width=92,
            height=46,
            corner_radius=13,
            font=(
                "Segoe UI",
                11,
                "bold"
            ),
            command=self.send
        )
        self.send_button.pack(
            side="left"
        )

    # ==================================================
    # STATE
    # ==================================================

    def set_busy_state(
        self,
        status
    ):
        self.state_label.configure(
            text=status
        )

        if status in {
            "Thinking",
            "Listening"
        }:
            self.send_button.configure(
                state="disabled"
            )
        else:
            self.send_button.configure(
                state="normal"
            )

    # ==================================================
    # ACTIONS
    # ==================================================

    def send(
        self,
        event=None
    ):
        message = self.entry.get().strip()

        if not message:
            return

        self.send_callback(
            message
        )

        self.entry.delete(
            0,
            "end"
        )

    def voice_input(self):
        if self.voice_callback:
            self.voice_callback()

    def stop_speaking(self):
        if self.stop_callback:
            self.stop_callback()

    def clear_chat(self):
        if self.clear_callback:
            self.clear_callback()

    def toggle_wake(self):
        if self.wake_callback:
            self.wake_callback(
                bool(
                    self.wake_switch.get()
                )
            )

    def toggle_voice_chat(self):
        if self.voice_chat_callback:
            self.voice_chat_callback(
                bool(
                    self.voice_chat_switch.get()
                )
            )
