import re

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

        # Remove wake-name / polite prefixes safely.
        # Example:
        # "Hey Jeroo, please open Chrome"
        # becomes:
        # "open chrome"
        prefix_patterns = [
            r"^(?:hey\s+)?(?:jeroo|jerro|jaroo)\b[\s,.:;!?-]*",
            r"^(?:please)\b[\s,.:;!?-]*",
            r"^(?:can you|could you|would you)\b[\s,.:;!?-]*",
        ]

        changed = True

        while changed:
            changed = False

            for pattern in prefix_patterns:

                new_cleaned = re.sub(
                    pattern,
                    "",
                    cleaned,
                    count=1,
                    flags=re.IGNORECASE
                )

                if new_cleaned != cleaned:
                    cleaned = new_cleaned.strip()
                    changed = True

        cleaned = re.sub(
            r"^[\s,.:;!?-]+",
            "",
            cleaned
        )

        cleaned = re.sub(
            r"\s+for me[\s,.:;!?-]*$",
            "",
            cleaned
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
        # BATTERY STATUS
        # ==================================================

        battery_phrases = [
            "battery",
            "battery status",
            "battery percentage",
            "battery level",
            "check battery",
            "check battery status",
            "how much battery do i have",
            "how much battery is left",
            "what is my battery",
            "what's my battery",
        ]

        if (
            cleaned in battery_phrases
            or (
                "battery" in cleaned
                and any(
                    word in cleaned
                    for word in [
                        "status",
                        "percentage",
                        "level",
                        "left",
                        "remaining",
                        "check",
                    ]
                )
            )
        ):

            return self.system.battery_status()

        # ==================================================
        # SCREENSHOT
        # ==================================================

        screenshot_phrases = [
            "screenshot",
            "take screenshot",
            "take a screenshot",
            "take screen shot",
            "capture screen",
            "capture my screen",
            "take a picture of my screen",
        ]

        if (
            cleaned in screenshot_phrases
            or "take screenshot" in cleaned
            or "take a screenshot" in cleaned
            or "capture screen" in cleaned
        ):

            return self.system.take_screenshot()

        # ==================================================
        # CURRENT TIME
        # ==================================================

        time_phrases = [
            "time",
            "what time is it",
            "what's the time",
            "tell me the time",
            "current time",
        ]

        if cleaned in time_phrases:

            return self.system.current_time()

        # ==================================================
        # CURRENT DATE
        # ==================================================

        date_phrases = [
            "date",
            "what is the date",
            "what's the date",
            "what day is it",
            "today's date",
            "todays date",
            "current date",
        ]

        if cleaned in date_phrases:

            return self.system.current_date()

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
        # SMART APP CONTROL
        # ==================================================

        # Natural open phrases such as:
        # open chrome / launch spotify / start my browser
        open_prefixes = [
            "open ",
            "launch ",
            "start ",
            "run ",
        ]

        for prefix in open_prefixes:
            if cleaned.startswith(prefix):
                app_name = cleaned[len(prefix):].strip()

                # Website and folder commands are handled above,
                # so anything reaching here can be treated as an app.
                if app_name:
                    return self.launcher.open_app(app_name)

        # Natural close phrases such as:
        # close spotify / quit chrome / exit vs code
        close_prefixes = [
            "close ",
            "quit ",
            "exit ",
            "stop ",
        ]

        for prefix in close_prefixes:
            if cleaned.startswith(prefix):
                app_name = cleaned[len(prefix):].strip()

                if app_name:
                    return self.launcher.close_app(app_name)

        # Switch/focus an application that is already open.
        switch_prefixes = [
            "switch to ",
            "go to ",
            "focus ",
            "show ",
            "bring up ",
        ]

        for prefix in switch_prefixes:
            if cleaned.startswith(prefix):
                app_name = cleaned[len(prefix):].strip()

                if app_name:
                    return self.launcher.switch_to_app(app_name)

        # Useful app discovery command.
        if cleaned in [
            "list apps",
            "list applications",
            "show installed apps",
            "what apps do i have",
        ]:
            apps = self.launcher.get_installed_apps()

            if not apps:
                return "I couldn't find any installed applications."

            preview = apps[:25]
            result = ", ".join(preview)

            if len(apps) > 25:
                result += f" and {len(apps) - 25} more"

            return f"I found these apps: {result}."

        # ==================================================
        # NOT A LOCAL COMMAND
        # ==================================================

        return None

