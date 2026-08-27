class ActionContext:
    """
    Small in-memory context for local PC actions.

    It intentionally does not persist to disk. This keeps phrases such as
    "close it" tied to the current Jeroo session instead of an old session.
    """

    def __init__(self):
        self.last_app = None
        self.last_safe_command = None

    def remember_app(self, app_name):
        app_name = " ".join(
            str(app_name).strip().split()
        )

        if app_name:
            self.last_app = app_name

    def remember_safe_command(self, command):
        command = " ".join(
            str(command).strip().split()
        )

        if command:
            self.last_safe_command = command

    def clear(self):
        self.last_app = None
        self.last_safe_command = None
