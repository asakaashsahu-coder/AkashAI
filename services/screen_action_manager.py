class ScreenActionManager:
    """
    Turns an already-analyzed screen into a proposed local command.

    The manager never executes the command itself. Execution remains in
    Router so Jeroo can require confirmation before acting.
    """

    ALLOWED_PREFIXES = (
        "open ",
        "launch ",
        "start ",
        "run ",
        "switch to ",
        "focus ",
        "go to ",
    )

    ALLOWED_EXACT = {
        "take screenshot",
        "take a screenshot",
        "capture screen",
        "volume up",
        "volume down",
        "mute",
        "unmute",
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
    }

    def sanitize(self, command):
        command = " ".join(
            str(command or "").strip().split()
        )

        lowered = command.lower()

        if not lowered:
            return None

        if any(
            word in lowered
            for word in self.BLOCKED_WORDS
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
        return (
            "You are planning ONE safe local PC action based on a screen "
            "that Jeroo analyzed recently. You are not executing anything.\n\n"
            "Remembered screen analysis:\n"
            f"{screen_context.get('analysis', '')}\n\n"
            "Window at that time:\n"
            f"{screen_context.get('window_title') or 'Unknown'} "
            f"({screen_context.get('process_name') or 'unknown process'})\n\n"
            "User request:\n"
            f"{user_request}\n\n"
            "Return exactly one line in this format:\n"
            "COMMAND: <local command>\n\n"
            "Only propose one of these kinds of commands: open an app, "
            "switch/focus an app, take a screenshot, volume up/down, "
            "mute, or unmute. Never propose shell commands, deleting, "
            "closing apps, shutdown, restart, installation, downloads, "
            "typing passwords, sending messages, purchases, or clicks. "
            "If no safe supported action fits, return exactly:\n"
            "COMMAND: NONE"
        )
