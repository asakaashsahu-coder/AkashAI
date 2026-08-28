import time


class ScreenContext:

    def __init__(
        self,
        lifetime_seconds=300
    ):
        self.lifetime_seconds = (
            lifetime_seconds
        )

        self.clear()

    # ==================================================
    # SAVE SCREEN CONTEXT
    # ==================================================

    def remember(
        self,
        analysis,
        original_request=None,
        window_title=None,
        process_name=None,
        app_name=None,
        app_type=None,
        analysis_mode=None
    ):
        analysis = str(
            analysis or ""
        ).strip()

        if not analysis:
            return

        self.analysis = analysis

        self.original_request = str(
            original_request or ""
        ).strip()

        self.window_title = str(
            window_title or ""
        ).strip()

        self.process_name = str(
            process_name or ""
        ).strip()

        self.app_name = str(
            app_name or ""
        ).strip()

        self.app_type = str(
            app_type or ""
        ).strip()

        self.analysis_mode = str(
            analysis_mode or ""
        ).strip()

        self.saved_at = time.time()

    # ==================================================
    # CHECK IF CONTEXT IS STILL FRESH
    # ==================================================

    def is_fresh(self):

        if (
            not self.analysis
            or self.saved_at is None
        ):
            return False

        return (
            time.time()
            - self.saved_at
            <= self.lifetime_seconds
        )

    # ==================================================
    # CONTEXT AGE
    # ==================================================

    def age_seconds(self):

        if self.saved_at is None:
            return None

        return max(
            0,
            int(
                time.time()
                - self.saved_at
            )
        )

    # ==================================================
    # GET SAVED CONTEXT
    # ==================================================

    def get(self):

        if not self.is_fresh():

            self.clear()

            return None

        return {

            "analysis":
                self.analysis,

            "original_request":
                self.original_request,

            "window_title":
                self.window_title,

            "process_name":
                self.process_name,

            "app_name":
                self.app_name,

            "app_type":
                self.app_type,

            "analysis_mode":
                self.analysis_mode,

            "age_seconds":
                self.age_seconds(),
        }

    # ==================================================
    # CHECK IF USER IS STILL ON SAME WINDOW
    # ==================================================

    def matches_window(
        self,
        window_info
    ):

        context = self.get()

        if (
            not context
            or not window_info
        ):
            return False

        current_process = str(
            window_info.get(
                "process"
            )
            or ""
        ).lower().strip()

        current_title = str(
            window_info.get(
                "title"
            )
            or ""
        ).lower().strip()

        remembered_process = str(
            context.get(
                "process_name"
            )
            or ""
        ).lower().strip()

        remembered_title = str(
            context.get(
                "window_title"
            )
            or ""
        ).lower().strip()

        return (
            current_process
            == remembered_process

            and

            current_title
            == remembered_title
        )

    # ==================================================
    # CLEAR SAVED SCREEN CONTEXT
    # ==================================================

    def clear(self):

        self.analysis = None

        self.window_title = None

        self.process_name = None

        self.app_name = None

        self.app_type = None

        self.analysis_mode = None

        self.original_request = None

        self.saved_at = None