
import customtkinter as ctk

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

        # Start as None.
        # They will be loaded after the GUI appears.

        self.router = None
        self.voice = None
        self.listener = None

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
        # LOAD CORE SYSTEMS AFTER GUI APPEARS
        # ==================================================

        self.after(
            100,
            self.initialize_core
        )

    # ==================================================
    # INITIALIZE CORE SYSTEMS
    # ==================================================

    def initialize_core(self):

        try:

            print(
                "Loading Jeroo core systems..."
            )

            from core.router import Router
            from core.voice import Voice
            from core.listener import Listener

            self.router = Router()
            self.voice = Voice()
            self.listener = Listener()

            print(
                "Jeroo core systems ready."
            )

        except Exception as e:

            print(
                "Core initialization error:",
                e
            )

    # ==================================================
    # CHECK CORE SYSTEMS
    # ==================================================

    def core_ready(self):

        if (
            self.router is None
            or self.voice is None
            or self.listener is None
        ):

            self.chat_area.add_message(
                "Jeroo",
                "I'm still starting up. Please try again in a moment."
            )

            return False

        return True

    # ==================================================
    # SEND MESSAGE
    # ==================================================

    def send_message(self, message):

        if not message.strip():
            return

        if not self.core_ready():
            return

        # ==================================================
        # SHOW USER MESSAGE
        # ==================================================

        self.chat_area.add_message(
            "You",
            message
        )

        # ==================================================
        # SHOW THINKING
        # ==================================================

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

        # ==================================================
        # REMOVE THINKING
        # ==================================================

        self.chat_area.remove_last_message()

        # ==================================================
        # SHOW RESPONSE
        # ==================================================

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

        if not self.core_ready():
            return

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

        # ==================================================
        # REMOVE LISTENING
        # ==================================================

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

        # ==================================================
        # THINKING
        # ==================================================

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

        # ==================================================
        # REMOVE THINKING
        # ==================================================

        self.chat_area.remove_last_message()

        # ==================================================
        # SHOW RESPONSE
        # ==================================================

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

        if self.voice is None:
            return

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

