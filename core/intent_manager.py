import re


class IntentManager:
    """
    Fast local intent classifier for Jeroo.

    The goal is not to replace the AI model. It decides which existing
    Jeroo subsystem should get a request first:
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

        # Natural saved-routine phrases:
        # "start coding mode" or just "coding mode".
        if routine_exists:
            natural = re.match(
                r"^(run|start|activate)\s+(.+)$",
                text
            )

            if natural:
                possible_name = natural.group(2).strip()

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
            ("remember ", "forget ")
        ):
            return "memory"

        # ==================================================
        # SCREEN VISION / DEICTIC CONTEXT
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
        }

        if text in screen_exact:
            return "screen"

        if any(
            word in text
            for word in [
                "my screen",
                "on screen",
                "on my display",
            ]
        ):
            return "screen"

        if (
            ("click here" in text or "click on" in text)
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
            "search google ",
            "search google for ",
            "search youtube ",
            "search youtube for ",
        )

        if text.startswith(
            action_starts
        ):
            # Only classify as multi-action if the sentence clearly
            # contains more than one requested action.
            if re.search(
                r"\s+(and then|then|and)\s+",
                text
            ):
                return "multi_action"

        # ==================================================
        # LOCAL PC COMMANDS
        # ==================================================

        if text.startswith(
            action_starts
        ):
            return "local_command"

        local_exact = {
            "volume up",
            "increase volume",
            "turn volume up",
            "volume down",
            "decrease volume",
            "turn volume down",
            "mute",
            "mute volume",
            "unmute",
            "take screenshot",
            "take a screenshot",
            "capture screen",
            "lock pc",
            "lock my pc",
            "lock computer",
            "lock my computer",
            "shutdown",
            "shut down",
            "restart",
            "reboot",
            "sleep",
            "go to sleep",
            "what time is it",
            "tell me the time",
            "current time",
            "what is the time",
            "what's the time",
            "whats the time",
            "what is today's date",
            "what is todays date",
            "today's date",
            "todays date",
            "what day is it",
            "current date",
            "list apps",
            "list applications",
            "what apps do i have",
        }

        if text in local_exact:
            return "local_command"

        if "battery" in text and any(
            word in text
            for word in [
                "percentage",
                "percent",
                "level",
                "status",
                "how much",
                "remaining",
            ]
        ):
            return "local_command"

        # ==================================================
        # NORMAL AI CONVERSATION
        # ==================================================

        return "ai"
