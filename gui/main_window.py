import threading
import time
from datetime import datetime

import customtkinter as ctk

from gui.header import Header
from gui.sidebar import Sidebar
from gui.chat_area import ChatArea
from gui.input_bar import InputBar
from services.chat_history import ChatHistoryManager
from services.settings_manager import SettingsManager
from gui.settings_panel import SettingsPanel
from gui.floating_assistant import FloatingAssistant


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
        self.shutdown_started = False

        # Reminder Soon state. The orb enters a softer glow during the
        # five minutes before the next reminder, then the existing
        # Reminder state takes over at the exact due time.
        self.reminder_soon_active = False
        self.reminder_soon_task = ""
        self.reminder_soon_job = None

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

        # ==================================================
        # FLOATING MINI ASSISTANT
        # ==================================================

        self.floating_assistant = FloatingAssistant(
            self,
            restore_callback=self.restore_full_window,
            exit_callback=self.exit_application,
            wake_callback=self.toggle_wake_from_floating,
            voice_chat_callback=self.toggle_voice_chat_from_floating
        )

        # Closing the full window now enters floating mode
        # instead of shutting Jerro down.
        self.protocol(
            "WM_DELETE_WINDOW",
            self.hide_to_floating
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
            "Reminder Soon": "#8fe9ff",
            "Reminder": "#fb7185",
            "Error": "#fb7185"
        }

        def update_status():
            if self.closing:
                return

            status_color = colors.get(
                status,
                "#4ade80"
            )

            self.header.set_status(
                status,
                status_color
            )

            try:
                self.floating_assistant.set_status(
                    status,
                    status_color
                )
            except Exception:
                pass

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

            try:
                self.router.automation.set_reminder_callback(
                    self._on_reminder_due
                )
            except Exception as error:
                print(
                    "Reminder callback setup error:",
                    error
                )

            self.voice = Voice(
                self.set_status
            )
            self.listener = Listener()

            self.set_status(
                "Ready"
            )

            self._start_reminder_soon_watch()

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
                    response,
                    message
                )
            )
        except Exception:
            pass

    def _show_response(self, response, message=""):
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
                    on_finish=self._after_speaking,
                    context=message
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

        self._restore_idle_status()

    def _restore_idle_status(self):
        if self.closing or self.busy:
            return

        if self.reminder_soon_active:
            self.set_status(
                "Reminder Soon"
            )
            return

        if self.wake_mode:
            self.set_status(
                "Wake Listening"
            )
        else:
            self.set_status(
                "Ready"
            )

    # ==================================================
    # REMINDER SOON WATCH
    # ==================================================

    def _start_reminder_soon_watch(self):
        self._cancel_reminder_soon_watch()
        self._check_upcoming_reminder()

    def _cancel_reminder_soon_watch(self):
        if self.reminder_soon_job is None:
            return

        try:
            self.after_cancel(
                self.reminder_soon_job
            )
        except Exception:
            pass

        self.reminder_soon_job = None

    def _next_active_reminder(self):
        if (
            self.router is None
            or not hasattr(
                self.router,
                "automation"
            )
        ):
            return None

        automation = self.router.automation

        try:
            with automation.lock:
                reminders = automation._load(
                    automation.reminders_file,
                    []
                )
        except Exception as error:
            print(
                "Reminder Soon read error:",
                error
            )
            return None

        now = datetime.now()
        upcoming = []

        for item in reminders:
            if item.get(
                "done",
                False
            ):
                continue

            try:
                due = datetime.fromisoformat(
                    item.get(
                        "due_at",
                        ""
                    )
                )
            except Exception:
                continue

            if due <= now:
                continue

            upcoming.append(
                (
                    due,
                    str(
                        item.get(
                            "task",
                            "Reminder"
                        )
                        or "Reminder"
                    ).strip()
                )
            )

        if not upcoming:
            return None

        upcoming.sort(
            key=lambda entry: entry[0]
        )

        return upcoming[0]

    def _check_upcoming_reminder(self):
        self.reminder_soon_job = None

        if self.closing:
            return

        next_reminder = self._next_active_reminder()
        should_glow = False
        task = ""

        if next_reminder is not None:
            due, task = next_reminder
            seconds_left = (
                due - datetime.now()
            ).total_seconds()

            # Soft reminder glow begins during the last five minutes.
            should_glow = (
                0 < seconds_left <= 300
            )

        changed = (
            should_glow
            != self.reminder_soon_active
        )

        task_changed = (
            should_glow
            and task
            != self.reminder_soon_task
        )

        self.reminder_soon_active = should_glow
        self.reminder_soon_task = (
            task
            if should_glow
            else ""
        )

        # Do not interrupt Listening, Thinking, Speaking or the full
        # Reminder alert. The softer glow is only an idle visual state.
        if (
            (changed or task_changed)
            and not self.busy
            and (
                self.voice is None
                or not self.voice.speaking()
            )
        ):
            self._restore_idle_status()

        try:
            self.reminder_soon_job = self.after(
                15000,
                self._check_upcoming_reminder
            )
        except Exception:
            self.reminder_soon_job = None

    # ==================================================
    # REMINDER ALERTS
    # ==================================================

    def _on_reminder_due(self, task):
        if self.closing:
            return

        try:
            self.after(
                0,
                lambda: self._present_reminder(
                    task
                )
            )
        except Exception:
            pass

    def _present_reminder(self, task):
        if self.closing:
            return

        self.reminder_soon_active = False
        self.reminder_soon_task = ""

        task = str(
            task
            or "Reminder"
        ).strip()

        message = (
            f"⏰ Reminder: {task}"
        )

        self.set_status(
            "Reminder"
        )

        try:
            self.chat_area.add_message(
                "Jeroo",
                message
            )

            self.chat_history.add_message(
                self.active_chat_id,
                "Jeroo",
                message
            )

            self.refresh_chat_history()
        except Exception as error:
            print(
                "Reminder chat error:",
                error
            )

        try:
            if (
                self.voice
                and self.settings_manager.get(
                    "voice_enabled",
                    True
                )
            ):
                self.after(
                    300,
                    lambda: self.voice.speak(
                        f"Reminder. {task}",
                        on_finish=self._after_speaking
                    )
                )
                return
        except Exception as error:
            print(
                "Reminder voice error:",
                error
            )

        self.after(
            1800,
            self._after_speaking
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
    # WINDOWS STARTUP / DIRECT ORB MODE
    # ==================================================

    def start_in_floating_mode(self):
        if self.closing:
            return

        try:
            self.withdraw()
            self.floating_assistant.show()

            print(
                "Jerro started in floating orb mode."
            )

        except Exception as error:
            print(
                "Startup orb mode error:",
                error
            )

    # ==================================================
    # FLOATING ASSISTANT MODE
    # ==================================================

    def hide_to_floating(self):
        if self.closing:
            return

        try:
            self.withdraw()

            self.floating_assistant.show()

            print(
                "Jerro entered floating mode."
            )

        except Exception as error:
            print(
                "Floating mode error:",
                error
            )

    def restore_full_window(self):
        if self.closing:
            return

        try:
            self.floating_assistant.hide()

            self.deiconify()
            self.lift()

            self.attributes(
                "-topmost",
                True
            )

            self.after(
                250,
                lambda: self.attributes(
                    "-topmost",
                    False
                )
            )

            self.focus_force()

        except Exception as error:
            print(
                "Restore full window error:",
                error
            )

    def toggle_wake_from_floating(self):
        if not self.core_ready():
            return

        enabled = not self.wake_mode

        try:
            if enabled:
                self.input_bar.wake_switch.select()
            else:
                self.input_bar.wake_switch.deselect()
        except Exception:
            pass

        self.toggle_wake_mode(
            enabled
        )

    def toggle_voice_chat_from_floating(self):
        if not self.core_ready():
            return

        enabled = not self.voice_chat_mode

        try:
            if enabled:
                self.input_bar.voice_chat_switch.select()
            else:
                self.input_bar.voice_chat_switch.deselect()
        except Exception:
            pass

        self.toggle_voice_chat(
            enabled
        )

    def exit_application(self):
        self.on_close()

    # ==================================================
    # CLOSE
    # ==================================================

    def on_close(self):
        if self.shutdown_started:
            return

        self.shutdown_started = True
        self.closing = True
        self.wake_mode = False
        self.voice_chat_mode = False
        self.voice_turn_active = False

        print("Shutting down Jerro...")

        try:
            self._cancel_auto_listen()
        except Exception:
            pass

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

        try:
            if self.floating_assistant:
                self.floating_assistant.prepare_shutdown()
        except Exception:
            pass

        try:
            self.withdraw()
        except Exception:
            pass

        try:
            self.after(
                20,
                self.quit
            )
        except Exception:
            try:
                self.quit()
            except Exception:
                pass

        print("Jerro shutdown complete.")

