class ScreenActionManager:
    """
    Turns an already-analyzed screen into a proposed local command.

    This manager never executes commands directly.
    Router remains responsible for confirmation and execution.
    """

    ALLOWED_PREFIXES = (
        "open ",
        "launch ",
        "start ",
        "run ",
        "switch to ",
        "focus ",
        "go to ",
        "search google ",
        "search google for ",
        "search youtube ",
        "search youtube for ",
    )

    ALLOWED_EXACT = {
        # Screen / audio
        "take screenshot",
        "take a screenshot",
        "capture screen",
        "volume up",
        "volume down",
        "mute",
        "unmute",

        # Media
        "play",
        "pause",
        "play music",
        "pause music",
        "next song",
        "next track",
        "previous song",
        "previous track",

        # Browser
        "new tab",
        "open new tab",
        "open a new tab",
        "close tab",
        "close this tab",
        "reopen tab",
        "reopen last tab",
        "refresh",
        "refresh page",
        "refresh this page",
        "reload",
        "reload page",
        "go back",
        "browser back",
        "go forward",
        "browser forward",
        "focus address bar",
        "focus the address bar",
        "find on page",
        "find on this page",

        # Window control
        "minimize",
        "minimize this window",
        "minimise this window",
        "maximize",
        "maximize this window",
        "maximise this window",
        "restore window",
        "restore this window",
    }

    BLOCKED_WORDS = {
        "shutdown",
        "restart",
        "reboot",
        "delete",
        "remove",
        "format",
        "erase",
        "uninstall",
        "kill",
        "taskkill",
        "powershell",
        "cmd",
        "terminal",
        "registry",
        "regedit",

        # Keep direct UI manipulation blocked for now.
        "click",
        "double click",
        "right click",
        "drag",
        "drop",
        "type ",
        "enter password",
        "password",
        "send message",
        "purchase",
        "buy ",
        "checkout",
        "pay ",
    }

    def sanitize(self, command):
        command = " ".join(
            str(command or "").strip().split()
        )

        lowered = command.lower()

        if not lowered:
            return None

        if any(
            blocked in lowered
            for blocked in self.BLOCKED_WORDS
        ):
            return None

        if lowered in self.ALLOWED_EXACT:
            return lowered

        if lowered.startswith(
            self.ALLOWED_PREFIXES
        ):
            return lowered

        return None

    def build_planning_prompt(
        self,
        screen_context,
        user_request
    ):
        app_name = (
            screen_context.get("app_name")
            or "Unknown app"
        )

        app_type = (
            screen_context.get("app_type")
            or "general"
        )

        window_title = (
            screen_context.get("window_title")
            or "Unknown window"
        )

        process_name = (
            screen_context.get("process_name")
            or "unknown process"
        )

        analysis = (
            screen_context.get("analysis")
            or ""
        )

        return (
            "You are planning exactly ONE safe local computer action "
            "for Jerro based on a screen that was analyzed recently.\n\n"

            "You are NOT executing anything.\n"
            "You must only choose from Jerro's supported local actions.\n\n"

            "Remembered screen analysis:\n"
            f"{analysis}\n\n"

            "Active app at the time:\n"
            f"App: {app_name}\n"
            f"Type: {app_type}\n"
            f"Window: {window_title}\n"
            f"Process: {process_name}\n\n"

            "User request:\n"
            f"{user_request}\n\n"

            "Return exactly one line using this format:\n"
            "COMMAND: <command>\n\n"

            "Supported safe actions include:\n"

            "- open, launch, start or run an application\n"
            "- switch to or focus an application\n"
            "- open a website through an already-supported app command\n"
            "- search Google or YouTube\n"
            "- take a screenshot\n"
            "- volume up, volume down, mute or unmute\n"
            "- play/pause media\n"
            "- next or previous media track\n"
            "- open, close or reopen a browser tab\n"
            "- refresh/reload the current browser page\n"
            "- browser back or forward\n"
            "- focus the browser address bar\n"
            "- open Find on the current page\n"
            "- minimize, maximize or restore the current window\n\n"

            "Examples of valid output:\n"
            "COMMAND: refresh this page\n"
            "COMMAND: open a new tab\n"
            "COMMAND: go back\n"
            "COMMAND: focus address bar\n"
            "COMMAND: minimize this window\n"
            "COMMAND: switch to visual studio code\n"
            "COMMAND: volume down\n"
            "COMMAND: next song\n\n"

            "Never propose:\n"
            "- shell or PowerShell commands\n"
            "- terminal commands\n"
            "- deleting or modifying files\n"
            "- shutdown, restart or sleep\n"
            "- installing or uninstalling software\n"
            "- arbitrary keyboard typing\n"
            "- passwords or credentials\n"
            "- sending messages or emails\n"
            "- purchases or payments\n"
            "- clicking buttons or coordinates\n"
            "- dragging UI elements\n"
            "- any action that Jerro does not explicitly support\n\n"

            "Do not invent controls that were not visible or supported.\n"

            "If the requested action cannot be safely mapped to one "
            "supported command, return exactly:\n"
            "COMMAND: NONE"
        )

    def extract_command(self, response):
        text = str(
            response or ""
        ).strip()

        if not text:
            return None

        for line in text.splitlines():
            line = line.strip()

            if not line.lower().startswith(
                "command:"
            ):
                continue

            command = line.split(
                ":",
                1
            )[1].strip()

            if command.lower() == "none":
                return None

            return self.sanitize(
                command
            )

        return None

    def plan(
        self,
        brain,
        screen_context,
        user_request
    ):
        if not screen_context:
            return None

        prompt = self.build_planning_prompt(
            screen_context,
            user_request
        )

        try:
            response = brain.get_response(
                prompt,
                memories=None
            )

        except Exception as error:
            print(
                "Screen action planning error:",
                error
            )
            return None

        return self.extract_command(
            response
        )