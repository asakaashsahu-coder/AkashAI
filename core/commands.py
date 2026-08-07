import subprocess

from services.app_launcher import AppLauncher
from services.project_manager import ProjectManager
from services.web_manager import WebManager
from services.system_control import SystemControl


class Commands:

    def __init__(self):

        self.launcher = AppLauncher()
        self.projects = ProjectManager()
        self.web = WebManager()
        self.system = SystemControl()

        # Confirmation states
        self.shutdown_confirmation = False
        self.restart_confirmation = False
        self.sleep_confirmation = False

    # ==================================================
    # MAIN COMMAND EXECUTOR
    # ==================================================

    def execute(self, message):

        message = message.lower().strip()

        # ==================================================
        # NORMALIZE VOICE / TEXT COMMAND
        # ==================================================

        cleaned = message

        for word in [
            "jeroo",
            "jaroo",
            "please",
            "can you",
            "could you",
            "would you",
            "hey",
            "for me",
        ]:

            cleaned = cleaned.replace(
                word,
                ""
            )

        cleaned = " ".join(
            cleaned.split()
        ).strip()

        # ==================================================
        # SHUTDOWN CONFIRMATION
        # ==================================================

        if self.shutdown_confirmation:

            if cleaned in [
                "yes",
                "yeah",
                "yep",
                "yes please",
                "sure",
                "confirm",
                "do it",
                "shutdown",
                "shut down",
                "turn it off",
            ]:

                self.shutdown_confirmation = False

                return self.system.shutdown()

            if cleaned in [
                "no",
                "nope",
                "no thanks",
                "cancel",
                "stop",
                "don't",
                "dont",
                "do not",
            ]:

                self.shutdown_confirmation = False

                return "Shutdown cancelled."

            return (
                "Please say yes to shut down "
                "or no to cancel."
            )

        # ==================================================
        # RESTART CONFIRMATION
        # ==================================================

        if self.restart_confirmation:

            if cleaned in [
                "yes",
                "yeah",
                "yep",
                "yes please",
                "sure",
                "confirm",
                "do it",
                "restart",
                "reboot",
            ]:

                self.restart_confirmation = False

                return self.system.restart()

            if cleaned in [
                "no",
                "nope",
                "no thanks",
                "cancel",
                "stop",
                "don't",
                "dont",
                "do not",
            ]:

                self.restart_confirmation = False

                return "Restart cancelled."

            return (
                "Please say yes to restart "
                "or no to cancel."
            )

        # ==================================================
        # SLEEP CONFIRMATION
        # ==================================================

        if self.sleep_confirmation:

            if cleaned in [
                "yes",
                "yeah",
                "yep",
                "yes please",
                "sure",
                "confirm",
                "do it",
                "sleep",
            ]:

                self.sleep_confirmation = False

                return self.system.sleep()

            if cleaned in [
                "no",
                "nope",
                "no thanks",
                "cancel",
                "stop",
                "don't",
                "dont",
                "do not",
            ]:

                self.sleep_confirmation = False

                return "Sleep cancelled."

            return (
                "Please say yes to sleep "
                "or no to cancel."
            )

        # ==================================================
        # SHUTDOWN REQUEST
        # ==================================================

        shutdown_phrases = [

            "shutdown",
            "shut down",

            "shutdown pc",
            "shut down pc",

            "shutdown my pc",
            "shut down my pc",

            "shutdown computer",
            "shut down computer",

            "shutdown my computer",
            "shut down my computer",

            "turn off my pc",
            "turn off pc",

            "turn off my computer",
            "turn off computer",

            "power off my pc",
            "power off pc",

            "power off my computer",
            "power off computer",
        ]

        if cleaned in shutdown_phrases:

            self.shutdown_confirmation = True

            return (
                "Are you sure you want to "
                "shut down your PC? "
                "Say yes or no."
            )

        # ==================================================
        # FLEXIBLE SHUTDOWN DETECTION
        # ==================================================

        shutdown_words = [
            "shutdown",
            "shut down",
            "power off",
            "turn off",
        ]

        computer_words = [
            "computer",
            "pc",
            "system",
            "laptop",
        ]

        has_shutdown_word = any(
            word in cleaned
            for word in shutdown_words
        )

        has_computer_word = any(
            word in cleaned
            for word in computer_words
        )

        if (
            has_shutdown_word
            and has_computer_word
        ):

            self.shutdown_confirmation = True

            return (
                "Are you sure you want to "
                "shut down your PC? "
                "Say yes or no."
            )

        # ==================================================
        # RESTART REQUEST
        # ==================================================

        restart_phrases = [

            "restart",
            "restart pc",
            "restart my pc",

            "restart computer",
            "restart my computer",

            "reboot",
            "reboot pc",
            "reboot my pc",

        ]

        if cleaned in restart_phrases:

            self.restart_confirmation = True

            return (
                "Are you sure you want to "
                "restart your PC? "
                "Say yes or no."
            )

        # ==================================================
        # CANCEL SHUTDOWN / RESTART
        # ==================================================

        if cleaned in [

            "cancel shutdown",
            "cancel shut down",
            "cancel restart",
            "cancel reboot",

        ]:

            self.shutdown_confirmation = False
            self.restart_confirmation = False

            return self.system.cancel_shutdown()

        # ==================================================
        # LOCK COMPUTER
        # ==================================================

        if cleaned in [

            "lock",
            "lock computer",
            "lock my computer",
            "lock pc",
            "lock my pc",
            "lock the computer",

        ]:

            return self.system.lock()

        # ==================================================
        # SLEEP REQUEST
        # ==================================================

        sleep_phrases = [

            "sleep",
            "sleep computer",
            "sleep my computer",

            "put computer to sleep",
            "put my computer to sleep",

            "put pc to sleep",
            "put my pc to sleep",

            "sleep pc",

        ]

        if cleaned in sleep_phrases:

            self.sleep_confirmation = True

            return (
                "Are you sure you want to "
                "put your PC to sleep? "
                "Say yes or no."
            )

        # ==================================================
        # VOLUME UP
        # ==================================================

        if cleaned in [

            "increase volume",
            "increase the volume",

            "volume up",

            "turn up volume",
            "turn up the volume",

            "make volume louder",
            "make it louder",

            "louder",

        ]:

            return self.system.volume_up()

        # ==================================================
        # VOLUME DOWN
        # ==================================================

        if cleaned in [

            "decrease volume",
            "decrease the volume",

            "volume down",

            "turn down volume",
            "turn down the volume",

            "make volume lower",
            "make it quieter",

            "quieter",

        ]:

            return self.system.volume_down()

        # ==================================================
        # MUTE
        # ==================================================

        if cleaned in [

            "mute",
            "mute computer",
            "mute the computer",

            "mute pc",
            "mute my pc",

            "mute audio",
            "mute sound",

        ]:

            return self.system.mute()

        # ==================================================
        # UNMUTE
        # ==================================================

        if cleaned in [

            "unmute",
            "unmute computer",
            "unmute the computer",

            "unmute pc",
            "unmute my pc",

            "unmute audio",
            "unmute sound",

        ]:

            return self.system.mute()

        # ==================================================
        # AKASHAI PROJECT
        # ==================================================

        if (
            "akashai project" in cleaned
            or "akash ai project" in cleaned
        ):

            return self.projects.open_project(
                "akashai"
            )

        # ==================================================
        # WINDOWS FOLDERS
        # ==================================================

        folders = [

            "desktop",
            "downloads",
            "documents",
            "pictures",
            "music",
            "videos",

        ]

        for folder in folders:

            if (
                f"open {folder}" in cleaned
                or f"open my {folder}" in cleaned
                or f"go to {folder}" in cleaned
                or f"go to my {folder}" in cleaned
            ):

                return self.projects.open_folder(
                    folder
                )

        # ==================================================
        # GOOGLE SEARCH
        # ==================================================

        google_prefixes = [

            "search google for ",
            "google search for ",
            "search for ",
            "search google ",

        ]

        for prefix in google_prefixes:

            if cleaned.startswith(prefix):

                query = cleaned[
                    len(prefix):
                ].strip()

                if query:

                    return self.web.google_search(
                        query
                    )

        # ==================================================
        # YOUTUBE SEARCH
        # ==================================================

        youtube_prefixes = [

            "search youtube for ",
            "youtube search for ",
            "search youtube ",

        ]

        for prefix in youtube_prefixes:

            if cleaned.startswith(prefix):

                query = cleaned[
                    len(prefix):
                ].strip()

                if query:

                    return self.web.youtube_search(
                        query
                    )

        # ==================================================
        # OPEN WEBSITES
        # ==================================================

        websites = [

            "google",
            "youtube",
            "github",
            "gmail",
            "chatgpt",
            "stackoverflow",

        ]

        for website in websites:

            if (
                cleaned == f"open {website}"
                or cleaned == f"go to {website}"
            ):

                return self.web.open_website(
                    website
                )

        # ==================================================
        # OPEN APPLICATION
        # ==================================================

        if cleaned.startswith("open "):

            app_name = cleaned[
                5:
            ].strip()

            if app_name:

                if self.launcher.is_supported(
                    app_name
                ):

                    return self.launcher.open_app(
                        app_name
                    )

        # ==================================================
        # CLOSE APPLICATION
        # ==================================================

        if cleaned.startswith("close "):

            app_name = cleaned[
                6:
            ].strip()

            process_names = {

                "notepad":
                    "notepad.exe",

                "chrome":
                    "chrome.exe",

                "google chrome":
                    "chrome.exe",

                "edge":
                    "msedge.exe",

                "microsoft edge":
                    "msedge.exe",

                "calculator":
                    "CalculatorApp.exe",

                "paint":
                    "mspaint.exe",

            }

            if app_name in process_names:

                try:

                    subprocess.run(
                        [
                            "taskkill",
                            "/IM",
                            process_names[
                                app_name
                            ],
                            "/F",
                        ],
                        capture_output=True,
                    )

                    return (
                        f"Closed {app_name}."
                    )

                except Exception as e:

                    return (
                        f"I couldn't close "
                        f"{app_name}: {e}"
                    )

        # ==================================================
        # NOT A LOCAL COMMAND
        # ==================================================

        return None