import time


class ScreenContext:
    """
    Short-lived text context from the last screen analysis.

    Jeroo does not keep the screenshot here. Only the AI's text analysis
    and foreground-window information are retained temporarily.
    """

    def __init__(self, lifetime_seconds=300):
        self.lifetime_seconds = lifetime_seconds

        self.analysis = None
        self.window_title = None
        self.process_name = None
        self.original_request = None
        self.saved_at = None

    def remember(
        self,
        analysis,
        original_request=None,
        window_title=None,
        process_name=None
    ):
        analysis = str(
            analysis
            or ""
        ).strip()

        if not analysis:
            return

        self.analysis = analysis
        self.original_request = str(
            original_request
            or ""
        ).strip()

        self.window_title = str(
            window_title
            or ""
        ).strip()

        self.process_name = str(
            process_name
            or ""
        ).strip()

        self.saved_at = time.time()

    def is_fresh(self):
        if not self.analysis or self.saved_at is None:
            return False

        return (
            time.time() - self.saved_at
            <= self.lifetime_seconds
        )

    def age_seconds(self):
        if self.saved_at is None:
            return None

        return max(
            0,
            int(time.time() - self.saved_at)
        )

    def get(self):
        if not self.is_fresh():
            self.clear()
            return None

        return {
            "analysis": self.analysis,
            "original_request": self.original_request,
            "window_title": self.window_title,
            "process_name": self.process_name,
            "age_seconds": self.age_seconds()
        }

    def clear(self):
        self.analysis = None
        self.window_title = None
        self.process_name = None
        self.original_request = None
        self.saved_at = None
