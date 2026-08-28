import re


class IntentManager:
    """
    Fast local intent classifier for Jeroo.

    This decides which Jeroo subsystem should receive a request first:
    routines, reminders/notes, screen vision, memory, PC commands,
    or normal AI conversation.
    """

    def classify(
        self,
        message,
        normalized,
        routine_exists=None
    ):
        text = normalized.strip().lower()

        if not text:
            return "ai"

        # ==================================================
        # ROUTINES
        # ==================================================

        routine_phrases = [
            "show routines",
            "show my routines",
            "list routines",
            "list my routines",
            "what routines do i have",
        ]

        if text in routine_phrases:
            return "routine"

        if re.match(
            r"^(create|make|save)\s+(a\s+)?routine\b",
            text
        ):
            return "routine"

        if re.match(
            r"^(delete|remove|show|describe)\s+"
            r"(my\s+)?routine\b",
            text
        ):
            return "routine"

        explicit_routine = re.match(
            r"^(run|start|activate)\s+"
            r"(my\s+)?routine\s+(.+)$",
            text
        )

        if explicit_routine:
            return "routine"

        # Natural saved-routine phrases such as:
        # "start coding mode" or just "coding mode".
        if routine_exists:

            natural = re.match(
                r"^(run|start|activate)\s+(.+)$",
                text
            )

            if natural:

                possible_name = (
                    natural.group(2).strip()
                )

                if routine_exists(
                    possible_name
                ):
                    return "routine"

            if text.endswith(" mode"):

                if routine_exists(
                    text
                ):
                    return "routine"

        # ==================================================
        # NOTES / REMINDERS
        # ==================================================

        automation_exact = {
            "show my notes",
            "show notes",
            "list my notes",
            "list notes",
            "clear my notes",
            "clear notes",
            "delete all notes",
            "show reminders",
            "show my reminders",
            "list reminders",
            "list my reminders",
            "clear reminders",
            "clear my reminders",
            "delete all reminders",
            "what do i have today",
            "what do i have for today",
            "what's on my schedule today",
            "whats on my schedule today",
            "today's reminders",
            "todays reminders",
        }

        if text in automation_exact:
            return "automation"

        if text.startswith((
            "create a note saying ",
            "create note saying ",
            "make a note saying ",
            "note that ",
            "save a note saying ",
            "remind me in ",
            "remind me at ",
            "remind me tomorrow ",
            "remind me tomorrow at ",
        )):
            return "automation"

        # ==================================================
        # ACTIVE WINDOW / CURRENT APP
        # ==================================================

        active_window_phrases = {
            "cancel close",
            "cancel closing",
            "do not close it",
            "dont close it",
            "confirm close this app",
            "confirm close current app",
            "yes close this app",
            "yes close it",
            "what app am i using",
            "what application am i using",
            "what app is this",
            "what window is active",
            "what is the active window",
            "which app is open",
            "which window am i on",
            "close this app",
            "close current app",
            "close this window",
            "close the current app",
        }

        if text in active_window_phrases:
            return "active_window"

        # ==================================================
        # MEMORY / CONVERSATION CONTEXT
        # ==================================================

        memory_exact = {
            "clear conversation",
            "clear conversation history",
            "forget this conversation",
            "new conversation",
            "start new conversation",
            "forget everything",
            "clear memory",
            "clear memories",
            "delete my memories",
            "what do you remember",
            "what do you remember about me",
            "what do you know about me",
            "show my memories",
            "show memories",
            "my memories",
        }

        if text in memory_exact:
            return "memory"

        if text.startswith(
            (
                "remember ",
                "forget ",
            )
        ):
            return "memory"

        # ==================================================
        # SCREEN VISION / SCREEN CONTEXT
        # ==================================================

        screen_exact = {
            "what is on my screen",
            "what's on my screen",
            "whats on my screen",
            "look at my screen",
            "analyze my screen",
            "analyse my screen",
            "explain my screen",
            "read my screen",
            "describe my screen",
            "help me with my screen",
            "what should i click here",
            "what do i click here",
            "explain this error",
            "what does this error mean",
            "help me with this",
            "help with this",
            "explain this",
            "fix this",
            "why is this not working",
            "what is this",
            "summarize this page",
            "summarise this page",
            "summarize this screen",
            "summarise this screen",
            "read this page",
            "explain this page",
        }

        if text in screen_exact:
            return "screen"

        if any(
            phrase in text
            for phrase in [
                "my screen",
                "on screen",
                "on my display",
                "this screen",
            ]
        ):
            return "screen"

        if (
            (
                "click here" in text
                or "click on" in text
            )
            and any(
                word in text
                for word in [
                    "what",
                    "where",
                    "which",
                    "should",
                ]
            )
        ):
            return "screen"

        # ==================================================
        # MULTI-ACTION PC AUTOMATION
        # ==================================================

        action_starts = (
            "open ",
            "launch ",
            "start ",
            "run ",
            "close ",
            "quit ",
            "exit ",
            "switch to ",
            "focus ",
            "go to ",
            "show ",
            "bring up ",
            "search google ",
            "search google for ",
            "search youtube ",
            "search youtube for ",
        )

        if text.startswith(
            action_starts
        ):

            # Only treat it as a multi-action request when
            # there are clearly several requested actions.
            if re.search(
                r"\s+(?:and then|then|and)\s+",
                text
            ):
                return "multi_action"

        # ==================================================
        # V1.6 BROWSER CONTROLS
        # ==================================================

        browser_exact = {
            "new tab",
            "open new tab",
            "open a new tab",
            "create new tab",
            "create a new tab",
            "new browser tab",
            "open another tab",

            "close tab",
            "close this tab",
            "close current tab",
            "close the tab",
            "close browser tab",

            "reopen tab",
            "reopen closed tab",
            "reopen the closed tab",
            "reopen last tab",
            "reopen the last tab",
            "restore last tab",
            "restore closed tab",

            "refresh",
            "refresh page",
            "refresh this page",
            "refresh current page",
            "reload",
            "reload page",
            "reload this page",
            "reload current page",

            "go back",
            "browser back",
            "go back one page",
            "go to previous page",
            "previous page",
            "back one page",

            "go forward",
            "browser forward",
            "go forward one page",
            "go to next page",
            "forward one page",

            "address bar",
            "focus address bar",
            "focus the address bar",
            "select address bar",
            "select the address bar",
            "go to address bar",
            "go to the address bar",

            "find on page",
            "find on this page",
            "search this page",
            "search on this page",
            "open find",
            "open find on page",
        }

        if text in browser_exact:
            return "local_command"

        # ==================================================
        # V1.6 MEDIA CONTROLS
        # ==================================================

        media_exact = {
            "play",
            "pause",
            "play music",
            "pause music",
            "play the music",
            "pause the music",
            "resume music",
            "resume the music",
            "play pause",
            "play or pause",
            "toggle playback",

            "next song",
            "next track",
            "skip song",
            "skip track",
            "skip this song",
            "skip this track",
            "play next song",
            "play the next song",

            "previous song",
            "previous track",
            "last song",
            "last track",
            "go back a song",
            "go back one song",
            "play previous song",
            "play the previous song",
        }

        if text in media_exact:
            return "local_command"

        # ==================================================
        # V1.6 ACTIVE WINDOW CONTROL
        # ==================================================

        window_control_exact = {
            "minimize",
            "minimise",
            "minimize this",
            "minimise this",
            "minimize window",
            "minimise window",
            "minimize this window",
            "minimise this window",
            "minimize current window",
            "minimise current window",

            "maximize",
            "maximise",
            "maximize this",
            "maximise this",
            "maximize window",
            "maximise window",
            "maximize this window",
            "maximise this window",
            "maximize current window",
            "maximise current window",
            "make this full screen",
            "make this fullscreen",

            "restore window",
            "restore this window",
            "restore current window",
            "restore this",
            "normal window",
            "make window normal",
            "make this window normal",
        }

        if text in window_control_exact:
            return "local_command"

        # ==================================================
        # NORMAL LOCAL PC COMMANDS
        # ==================================================

        if text.startswith(
            action_starts
        ):
            return "local_command"

        local_exact = {
            # Volume
            "volume up",
            "increase volume",
            "increase the volume",
            "turn volume up",
            "turn up volume",
            "turn up the volume",
            "make volume louder",
            "make it louder",
            "louder",

            "volume down",
            "decrease volume",
            "decrease the volume",
            "turn volume down",
            "turn down volume",
            "turn down the volume",
            "make volume lower",
            "make it quieter",
            "quieter",

            "mute",
            "mute volume",
            "mute computer",
            "mute the computer",
            "mute pc",
            "mute my pc",
            "mute audio",
            "mute sound",

            "unmute",
            "unmute computer",
            "unmute the computer",
            "unmute pc",
            "unmute my pc",
            "unmute audio",
            "unmute sound",

            # Screenshot
            "screenshot",
            "take screenshot",
            "take a screenshot",
            "take screen shot",
            "capture screen",
            "capture my screen",
            "take a picture of my screen",

            # Lock
            "lock",
            "lock pc",
            "lock my pc",
            "lock computer",
            "lock my computer",
            "lock the computer",

            # Power
            "shutdown",
            "shut down",
            "restart",
            "reboot",
            "sleep",
            "go to sleep",

            # Time
            "time",
            "what time is it",
            "tell me the time",
            "current time",
            "what is the time",
            "what's the time",
            "whats the time",

            # Date
            "date",
            "what is the date",
            "what's the date",
            "what is today's date",
            "what is todays date",
            "today's date",
            "todays date",
            "what day is it",
            "current date",

            # Apps
            "list apps",
            "list applications",
            "show installed apps",
            "what apps do i have",
        }

        if text in local_exact:
            return "local_command"

        # ==================================================
        # BATTERY
        # ==================================================

        battery_exact = {
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
        }

        if text in battery_exact:
            return "local_command"

        if (
            "battery" in text
            and any(
                word in text
                for word in [
                    "percentage",
                    "percent",
                    "level",
                    "status",
                    "how much",
                    "remaining",
                    "left",
                    "check",
                ]
            )
        ):
            return "local_command"

        # ==================================================
        # NORMAL AI CONVERSATION
        # ==================================================

        return "ai"