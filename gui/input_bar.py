import customtkinter as ctk


class InputBar(ctk.CTkFrame):

    def __init__(
        self,
        parent,
        send_callback,
        voice_callback=None,
        clear_callback=None,
        stop_callback=None
    ):

        super().__init__(parent)

        # Store callbacks
        self.send_callback = send_callback
        self.voice_callback = voice_callback
        self.clear_callback = clear_callback
        self.stop_callback = stop_callback

        # ==================================================
        # MESSAGE INPUT
        # ==================================================

        self.entry = ctk.CTkEntry(
            self,
            placeholder_text="Talk to Jeroo...",
            height=42
        )

        self.entry.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(10, 5),
            pady=10
        )

        self.entry.bind(
            "<Return>",
            self.send
        )

        # ==================================================
        # MICROPHONE BUTTON
        # ==================================================

        self.mic_button = ctk.CTkButton(
            self,
            text="🎤",
            width=50,
            height=42,
            command=self.voice_input
        )

        self.mic_button.pack(
            side="left",
            padx=5,
            pady=10
        )

        # ==================================================
        # STOP BUTTON
        # ==================================================

        self.stop_button = ctk.CTkButton(
            self,
            text="🛑 Stop",
            width=80,
            height=42,
            command=self.stop_speaking
        )

        self.stop_button.pack(
            side="left",
            padx=5,
            pady=10
        )

        # ==================================================
        # SEND BUTTON
        # ==================================================

        self.send_button = ctk.CTkButton(
            self,
            text="Send",
            width=80,
            height=42,
            command=self.send
        )

        self.send_button.pack(
            side="left",
            padx=5,
            pady=10
        )

        # ==================================================
        # CLEAR BUTTON
        # ==================================================

        self.clear_button = ctk.CTkButton(
            self,
            text="Clear",
            width=80,
            height=42,
            command=self.clear_chat
        )

        self.clear_button.pack(
            side="right",
            padx=(5, 10),
            pady=10
        )

    # ==================================================
    # SEND MESSAGE
    # ==================================================

    def send(self, event=None):

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

    # ==================================================
    # VOICE INPUT
    # ==================================================

    def voice_input(self):

        if self.voice_callback:

            self.voice_callback()

    # ==================================================
    # STOP SPEAKING
    # ==================================================

    def stop_speaking(self):

        if self.stop_callback:

            self.stop_callback()

    # ==================================================
    # CLEAR CHAT
    # ==================================================

    def clear_chat(self):

        if self.clear_callback:

            self.clear_callback()