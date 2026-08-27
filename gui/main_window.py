import threading
import time

import customtkinter as ctk

from gui.header import Header
from gui.sidebar import Sidebar
from gui.chat_area import ChatArea
from gui.input_bar import InputBar
from services.chat_history import ChatHistoryManager
from services.settings_manager import SettingsManager
from gui.settings_panel import SettingsPanel


class MainWindow(ctk.CTk):

    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("Jeroo AI")
        self.geometry("1260x760")
        self.minsize(980, 650)

        self.configure(
            fg_color="#090d16"
        )

        self.router = None
        self.voice = None
        self.listener = None

        self.settings_manager = SettingsManager()
        self.saved_settings = self.settings_manager.get_all()

        self.chat_history = ChatHistoryManager()
        self.active_chat = self.chat_history.get_active_chat()
        self.active_chat_id = self.active_chat["id"]

        self.busy = False
        self.wake_mode = False
        self.wake_thread = None

        # Voice Chat is an optional conversational loop:
        # listen -> think -> speak -> listen again.
        self.voice_chat_mode = False
        self.voice_turn_active = False
        self.auto_listen_job = None

        self.closing = False

        # ==================================================
        # HEADER
        # ==================================================

        self.header = Header(self)
        self.header.pack(
            fill="x",
            padx=14,
            pady=(14, 0)
        )

        # ==================================================
        # MAIN LAYOUT
        # ==================================================

        self.main_frame = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )
        self.main_frame.pack(
            fill="both",
            expand=True,
            padx=14,
            pady=14
        )

        self.sidebar = Sidebar(
            self.main_frame,
            new_chat_callback=self.new_conversation,
            action_callback=self.run_quick_action,
            chat_open_callback=self.open_saved_chat,
            chat_delete_callback=self.delete_saved_chat,
            settings_callback=self.open_settings
        )
        self.sidebar.pack(
            side="left",
            fill="y",
            padx=(0, 12)
        )

        self.refresh_chat_history()

        self.right_frame = ctk.CTkFrame(
            self.main_frame,
            fg_color="#0d1320",
            corner_radius=18,
            border_width=1,
            border_color="#1c2738"
        )
        self.right_frame.pack(
            side="left",
            fill="both",
            expand=True
        )

        self.chat_area = ChatArea(
            self.right_frame
        )
        self.chat_area.pack(
            fill="both",
            expand=True,
            padx=12,
            pady=(12, 6)
        )

        self.input_bar = InputBar(
            self.right_frame,
            self.send_message,
            self.voice_input,
            self.clear_chat,
            self.stop_speaking,
            self.toggle_wake_mode,
            self.toggle_voice_chat
        )
        self.input_bar.pack(
            fill="x",
            padx=12,
            pady=(6, 12)
        )

        self.protocol(
            "WM_DELETE_WINDOW",
            self.on_close
        )

        self.apply_saved_ui_settings()

        self.after(
            100,
            self.initialize_core
        )

    # ==================================================
    # QUICK ACTIONS
    # ==================================================

    def run_quick_action(self, command):
        if not command:
            return

        self.send_message(
            command
        )

    # ==================================================
    # STATUS
    # ==================================================

    def set_status(self, status):
        colors = {
            "Starting": "#f59e0b",
            "Ready": "#4ade80",
            "Wake Listening": "#38bdf8",
            "Listening": "#60a5fa",
            "Thinking": "#c084fc",
            "Speaking": "#facc15",
            "Error": "#fb7185"
        }

        def update_status():
            if self.closing:
                return

            self.header.set_status(
                status,
                colors.get(
                    status,
                    "#4ade80"
                )
            )

            try:
                self.input_bar.set_busy_state(
                    status
                )
            except Exception:
                pass

        try:
            self.after(
                0,
                update_status
            )
        except Exception:
            pass

    # ==================================================
    # INITIALIZE CORE
    # ==================================================

    def initialize_core(self):
        self.set_status(
            "Starting"
        )

        try:
            print(
                "Loading Jeroo core systems..."
            )

            from core.router import Router
            from core.voice import Voice
            from core.listener import Listener

            self.router = Router()
            self.voice = Voice(
                self.set_status
            )
            self.listener = Listener()

            self.set_status(
                "Ready"
            )

            self.load_active_chat()

            if self.settings_manager.get(
                "wake_phrase_enabled",
                False
            ):
                try:
                    self.input_bar.wake_switch.select()
                    self.toggle_wake_mode(True)
                except Exception as error:
                    print(
                        "Wake startup setting error:",
                        error
                    )

            print(
                "Jeroo core systems ready."
            )

        except Exception as e:
            self.set_status(
                "Error"
            )
            print(
                "Core initialization error:",
                e
            )

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
    # TEXT / AI RESPONSE
    # ==================================================

    def send_message(self, message):
        message = message.strip()

        if not message or self.busy:
            return

        # A typed turn is not part of the automatic voice loop.
        self.voice_turn_active = False
        self._cancel_auto_listen()

        if not self.core_ready():
            return

        if (
            self.voice
            and self.voice.speaking()
        ):
            self.voice.stop(
                update_status=False
            )

        self.chat_area.add_message(
            "You",
            message
        )

        self.chat_history.add_message(
            self.active_chat_id,
            "You",
            message
        )

        self.refresh_chat_history()

        self._start_thinking(
            message
        )

    def _start_thinking(self, message):
        self.busy = True
        self.set_status(
            "Thinking"
        )

        self.chat_area.add_typing_indicator()

        thread = threading.Thread(
            target=self._get_response_thread,
            args=(message,),
            daemon=True
        )
        thread.start()

    def _get_response_thread(self, message):
        try:
            response = self.router.get_response(
                message
            )
        except Exception as e:
            response = f"Error: {e}"

        try:
            self.after(
                0,
                lambda: self._show_response(
                    response
                )
            )
        except Exception:
            pass

    def _show_response(self, response):
        if self.closing:
            return

        self.chat_area.remove_typing_indicator()

        self.chat_area.add_message(
            "Jeroo",
            response
        )

        self.chat_history.add_message(
            self.active_chat_id,
            "Jeroo",
            response
        )

        self.refresh_chat_history()

        self.busy = False

        try:
            if self.settings_manager.get(
                "voice_enabled",
                True
            ):
                self.voice.speak(
                    response,
                    on_finish=self._after_speaking
                )
            else:
                self._after_speaking()
        except Exception as e:
            print(
                "Voice error:",
                e
            )
            self._after_speaking()

    def _after_speaking(self):
        if self.closing:
            return

        # If this exchange started from voice and Voice Chat is enabled,
        # automatically listen for the user's next turn after a short pause.
        if (
            self.voice_chat_mode
            and self.voice_turn_active
            and not self.busy
        ):
            self.set_status(
                "Ready"
            )

            self._cancel_auto_listen()

            self.auto_listen_job = self.after(
                550,
                self._continue_voice_chat
            )

            return

        if (
            self.wake_mode
            and not self.busy
        ):
            self.set_status(
                "Wake Listening"
            )
        else:
            self.set_status(
                "Ready"
            )

    # ==================================================
    # MANUAL VOICE INPUT
    # ==================================================

    def voice_input(self):
        if self.busy:
            return

        self.voice_turn_active = True
        self._cancel_auto_listen()

        if not self.core_ready():
            return

        if (
            self.voice
            and self.voice.speaking()
        ):
            self.voice.stop(
                update_status=False
            )

        if self.listener:
            self.listener.cancel()

        self.busy = True
        self.set_status(
            "Listening"
        )

        self.chat_area.add_listening_indicator()

        thread = threading.Thread(
            target=self._listen_thread,
            daemon=True
        )
        thread.start()

    def _listen_thread(self):
        time.sleep(
            0.12
        )

        try:
            text = self.listener.listen()
            error = self.listener.last_error
        except Exception as e:
            print(
                "Microphone error:",
                e
            )
            text = ""
            error = "microphone_error"

        try:
            self.after(
                0,
                lambda: self._finish_listening(
                    text,
                    error
                )
            )
        except Exception:
            pass

    def _finish_listening(
        self,
        text,
        error=""
    ):
        if self.closing:
            return

        self.chat_area.remove_listening_indicator()

        if not text:
            if error == "cancelled":
                message = "Listening stopped."
            elif error == "service_error":
                message = (
                    "Speech recognition is unavailable right now."
                )
            elif error == "microphone_error":
                message = (
                    "I couldn't access the microphone."
                )
            elif error == "no_speech":
                message = (
                    "I didn't hear anything. Try speaking a little "
                    "closer to the microphone."
                )
            else:
                message = (
                    "I couldn't understand that. Please try again."
                )

            self.chat_area.add_message(
                "Jeroo",
                message
            )

            self.busy = False

            # A silent follow-up should end the automatic conversation
            # rather than repeatedly reopening the microphone.
            if self.voice_chat_mode:
                self.voice_turn_active = False

            self._after_speaking()
            return

        self.chat_area.add_message(
            "You",
            text
        )

        self.chat_history.add_message(
            self.active_chat_id,
            "You",
            text
        )

        self.refresh_chat_history()

        self.busy = False

        self._start_thinking(
            text
        )

    # ==================================================
    # VOICE CHAT MODE
    # ==================================================

    def toggle_voice_chat(self, enabled):
        self.voice_chat_mode = bool(
            enabled
        )

        if self.voice_chat_mode:
            print(
                "Voice Chat enabled."
            )

            self.chat_area.add_message(
                "Jeroo",
                "Voice Chat is on. After I answer a voice question, "
                "I'll automatically listen for your next reply."
            )

        else:
            print(
                "Voice Chat disabled."
            )

            self.voice_turn_active = False
            self._cancel_auto_listen()

            if not self.busy:
                self._after_speaking()

    def _continue_voice_chat(self):
        self.auto_listen_job = None

        if (
            not self.voice_chat_mode
            or not self.voice_turn_active
            or self.busy
            or self.closing
        ):
            return

        if (
            self.voice
            and self.voice.speaking()
        ):
            return

        self.voice_input()

    def _cancel_auto_listen(self):
        if self.auto_listen_job is None:
            return

        try:
            self.after_cancel(
                self.auto_listen_job
            )
        except Exception:
            pass

        self.auto_listen_job = None

    # ==================================================
    # WAKE PHRASE MODE
    # ==================================================

    def toggle_wake_mode(
        self,
        enabled
    ):
        if not self.core_ready():
            try:
                self.input_bar.wake_switch.deselect()
            except Exception:
                pass
            return

        self.wake_mode = enabled

        if enabled:
            print(
                "Wake phrase enabled: say 'Hey Jeroo'."
            )

            self.chat_area.add_message(
                "Jeroo",
                "Wake mode is on. Say “Hey Jeroo” when you need me."
            )

            self._start_wake_thread()

        else:
            print(
                "Wake phrase disabled."
            )

            if self.listener:
                self.listener.cancel()

            if not self.busy:
                self.set_status(
                    "Ready"
                )

    def _start_wake_thread(self):
        if (
            self.wake_thread
            and self.wake_thread.is_alive()
        ):
            return

        self.wake_thread = threading.Thread(
            target=self._wake_loop,
            daemon=True
        )
        self.wake_thread.start()

    def _wake_loop(self):
        while (
            self.wake_mode
            and not self.closing
        ):
            if self.busy:
                time.sleep(
                    0.25
                )
                continue

            if (
                self.voice
                and self.voice.speaking()
            ):
                time.sleep(
                    0.25
                )
                continue

            self.set_status(
                "Wake Listening"
            )

            try:
                detected = (
                    self.listener.listen_for_wake_word()
                )
            except Exception as e:
                print(
                    "Wake listener error:",
                    e
                )
                detected = False

            if (
                not self.wake_mode
                or self.closing
            ):
                break

            if detected:
                print(
                    "✅ Wake phrase detected."
                )

                try:
                    self.after(
                        0,
                        self._wake_activated
                    )
                except Exception:
                    pass

                while (
                    self.wake_mode
                    and not self.closing
                    and (
                        self.busy
                        or (
                            self.voice
                            and self.voice.speaking()
                        )
                    )
                ):
                    time.sleep(
                        0.25
                    )

            else:
                time.sleep(
                    0.15
                )

    def _wake_activated(self):
        if (
            self.busy
            or self.closing
        ):
            return

        self.chat_area.add_message(
            "Jeroo",
            "Yes? 🎤"
        )

        self.after(
            250,
            self.voice_input
        )

    # ==================================================
    # STOP
    # ==================================================

    def stop_speaking(self):
        if not self.core_ready():
            return

        self.voice_turn_active = False
        self._cancel_auto_listen()

        try:
            self.listener.cancel()
        except Exception:
            pass

        try:
            self.voice.stop(
                update_status=False
            )
        except Exception as e:
            print(
                "Stop voice error:",
                e
            )

        if not self.busy:
            self._after_speaking()

    # ==================================================
    # CLEAR CHAT
    # ==================================================

    def clear_chat(self):
        self.chat_area.clear()
        self.chat_area.show_welcome()

    # ==================================================
    # CHAT HISTORY
    # ==================================================

    def refresh_chat_history(self):
        try:
            self.sidebar.load_chats(
                self.chat_history.list_chats(
                    limit=30
                ),
                self.active_chat_id
            )
        except Exception as error:
            print(
                "Chat history sidebar error:",
                error
            )

    def load_active_chat(self):
        chat = self.chat_history.get_chat(
            self.active_chat_id
        )

        if not chat:
            chat = self.chat_history.create_chat()
            self.active_chat_id = chat["id"]

        self.chat_area.load_messages(
            chat.get(
                "messages",
                []
            )
        )

        self.refresh_chat_history()

    def new_conversation(self):
        if self.busy:
            return

        chat = self.chat_history.create_chat()

        self.active_chat_id = chat["id"]

        self.chat_area.clear()
        self.chat_area.show_welcome()

        self.refresh_chat_history()

    def open_saved_chat(self, chat_id):
        if self.busy:
            return

        chat = self.chat_history.get_chat(
            chat_id
        )

        if not chat:
            return

        self.chat_history.set_active_chat(
            chat_id
        )

        self.active_chat_id = chat_id

        self.chat_area.load_messages(
            chat.get(
                "messages",
                []
            )
        )

        self.refresh_chat_history()

    def delete_saved_chat(self, chat_id):
        if self.busy:
            return

        was_active = (
            chat_id == self.active_chat_id
        )

        deleted = self.chat_history.delete_chat(
            chat_id
        )

        if not deleted:
            return

        if was_active:
            chat = self.chat_history.get_active_chat()
            self.active_chat_id = chat["id"]

            self.chat_area.load_messages(
                chat.get(
                    "messages",
                    []
                )
            )

        self.refresh_chat_history()

    # ==================================================
    # SETTINGS
    # ==================================================

    def apply_saved_ui_settings(self):
        settings = self.settings_manager.get_all()

        appearance = settings.get(
            "appearance",
            "Dark"
        )

        if appearance == "System":
            ctk.set_appearance_mode(
                "system"
            )
        else:
            ctk.set_appearance_mode(
                "dark"
            )

        scales = {
            "90%": 0.90,
            "100%": 1.00,
            "110%": 1.10
        }

        ctk.set_widget_scaling(
            scales.get(
                settings.get(
                    "ui_scale",
                    "100%"
                ),
                1.00
            )
        )

    def open_settings(self):
        try:
            if (
                hasattr(self, "settings_window")
                and self.settings_window
                and self.settings_window.winfo_exists()
            ):
                self.settings_window.focus()
                return
        except Exception:
            pass

        self.settings_window = SettingsPanel(
            self,
            self.settings_manager,
            on_apply=self.apply_settings,
            on_clear_history=self.clear_all_chat_history,
            on_clear_memory=self.clear_long_term_memory
        )

    def apply_settings(self, values):
        appearance = values.get(
            "appearance",
            "Dark"
        )

        if appearance == "System":
            ctk.set_appearance_mode(
                "system"
            )
        else:
            ctk.set_appearance_mode(
                "dark"
            )

        scales = {
            "90%": 0.90,
            "100%": 1.00,
            "110%": 1.10
        }

        ctk.set_widget_scaling(
            scales.get(
                values.get(
                    "ui_scale",
                    "100%"
                ),
                1.00
            )
        )

        wake_enabled = values.get(
            "wake_phrase_enabled",
            False
        )

        try:
            if wake_enabled and not self.wake_mode:
                self.input_bar.wake_switch.select()
                self.toggle_wake_mode(True)

            elif not wake_enabled and self.wake_mode:
                self.input_bar.wake_switch.deselect()
                self.toggle_wake_mode(False)

        except Exception as error:
            print(
                "Wake settings error:",
                error
            )

    def clear_all_chat_history(self):
        if self.busy:
            return

        self.settings_manager.clear_chat_history()

        chat = self.chat_history.create_chat()
        self.active_chat_id = chat["id"]

        self.chat_area.clear()
        self.chat_area.show_welcome()
        self.refresh_chat_history()

    def clear_long_term_memory(self):
        # Prefer Jerro's own memory command because it knows the
        # current memory implementation. Fall back to local JSON.
        try:
            if self.router:
                response = self.router.handle_memory_command(
                    "clear memory"
                )

                if response is not None:
                    return True
        except Exception as error:
            print(
                "Memory clear command error:",
                error
            )

        return self.settings_manager.clear_memory_file()

    # ==================================================
    # CLOSE
    # ==================================================

    def on_close(self):
        self.closing = True
        self.wake_mode = False
        self.voice_chat_mode = False
        self.voice_turn_active = False
        self._cancel_auto_listen()

        try:
            if self.listener:
                self.listener.cancel()
        except Exception:
            pass

        try:
            if self.voice:
                self.voice.stop(
                    update_status=False
                )
        except Exception:
            pass

        self.destroy()
