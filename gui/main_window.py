import customtkinter as ctk

from core.router import Router
from core.voice import Voice
from core.listener import Listener

from gui.header import Header
from gui.sidebar import Sidebar
from gui.chat_area import ChatArea
from gui.input_bar import InputBar


class MainWindow(ctk.CTk):

    def __init__(self):

        super().__init__()

        # ==================================================
        # WINDOW SETTINGS
        # ==================================================

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("Jeroo AI")
        self.geometry("1200x700")

        # ==================================================
        # CORE SYSTEMS
        # ==================================================

        self.router = Router()
        self.voice = Voice()
        self.listener = Listener()

        # ==================================================
        # HEADER
        # ==================================================

        self.header = Header(self)

        self.header.pack(
            fill="x"
        )

        # ==================================================
        # MAIN FRAME
        # ==================================================

        self.main_frame = ctk.CTkFrame(
            self
        )

        self.main_frame.pack(
            fill="both",
            expand=True
        )

        # ==================================================
        # SIDEBAR
        # ==================================================

        self.sidebar = Sidebar(
            self.main_frame
        )

        self.sidebar.pack(
            side="left",
            fill="y"
        )

        # ==================================================
        # RIGHT SIDE
        # ==================================================

        self.right_frame = ctk.CTkFrame(
            self.main_frame
        )

        self.right_frame.pack(
            side="left",
            fill="both",
            expand=True
        )

        # ==================================================
        # CHAT AREA
        # ==================================================

        self.chat_area = ChatArea(
            self.right_frame
        )

        self.chat_area.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=(10, 0)
        )

        # ==================================================
        # INPUT BAR
        # ==================================================

        self.input_bar = InputBar(
            self.right_frame,
            self.send_message,
            self.voice_input,
            self.clear_chat,
            self.stop_speaking
        )

        self.input_bar.pack(
            fill="x",
            padx=10,
            pady=10
        )

    # ==================================================
    # SEND MESSAGE
    # ==================================================

    def send_message(self, message):

        if not message.strip():
            return

        # Show user message
        self.chat_area.add_message(
            "You",
            message
        )

        # Show thinking
        self.chat_area.add_message(
            "Jeroo",
            "Thinking..."
        )

        self.update()

        # ==================================================
        # GET AI RESPONSE
        # ==================================================

        try:

            response = self.router.get_response(
                message
            )

        except Exception as e:

            response = f"Error: {e}"

        # Remove Thinking...
        self.chat_area.remove_last_message()

        # Show response
        self.chat_area.add_message(
            "Jeroo",
            response
        )

        self.update()

        # ==================================================
        # SPEAK RESPONSE
        # ==================================================

        try:

            self.voice.speak(
                response
            )

        except Exception as e:

            print(
                "Voice error:",
                e
            )

    # ==================================================
    # VOICE INPUT
    # ==================================================

    def voice_input(self):

        self.chat_area.add_message(
            "Jeroo",
            "🎤 Listening..."
        )

        self.update()

        # ==================================================
        # LISTEN
        # ==================================================

        try:

            text = self.listener.listen()

        except Exception as e:

            print(
                "Microphone error:",
                e
            )

            text = None

        # Remove Listening...
        self.chat_area.remove_last_message()

        # ==================================================
        # NOTHING HEARD
        # ==================================================

        if not text:

            self.chat_area.add_message(
                "Jeroo",
                "I couldn't understand that. Please try again."
            )

            return

        # ==================================================
        # SHOW USER SPEECH
        # ==================================================

        self.chat_area.add_message(
            "You",
            text
        )

        # Thinking
        self.chat_area.add_message(
            "Jeroo",
            "Thinking..."
        )

        self.update()

        # ==================================================
        # GET RESPONSE
        # ==================================================

        try:

            response = self.router.get_response(
                text
            )

        except Exception as e:

            response = f"Error: {e}"

        # Remove Thinking...
        self.chat_area.remove_last_message()

        # Show Jeroo response
        self.chat_area.add_message(
            "Jeroo",
            response
        )

        self.update()

        # ==================================================
        # SPEAK RESPONSE
        # ==================================================

        try:

            self.voice.speak(
                response
            )

        except Exception as e:

            print(
                "Voice error:",
                e
            )

    # ==================================================
    # STOP JEROO SPEAKING
    # ==================================================

    def stop_speaking(self):

        try:

            self.voice.stop()

        except Exception as e:

            print(
                "Stop voice error:",
                e
            )

    # ==================================================
    # CLEAR CHAT
    # ==================================================

    def clear_chat(self):

        self.chat_area.clear()