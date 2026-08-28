import re


class SmartRouter:

    SCREEN_PHRASES = (
        "my screen",
        "this screen",
        "on screen",
        "on my screen",
        "what am i looking at",
        "what do you see",
        "look at my screen",
        "check my screen",
        "screen error",
        "visible error",
        "this error",
        "explain this error",
        "why is this not working",
        "what should i click",
        "where should i click",
        "summarize this page",
        "summarise this page",
        "summarize this screen",
        "summarise this screen",
        "explain this page",
        "read this page",
        "what is this page",
        "what changed on screen",
        "what changed here",
    )

    # ==================================================
    # MAIN ROUTER
    # ==================================================

    def rule_route(
        self,
        message
    ):
        text = " ".join(
            str(
                message or ""
            ).lower().split()
        )

        if not text:
            return None

        # ----------------------------------------------
        # SCREEN INTELLIGENCE
        # ----------------------------------------------

        if any(
            term in text
            for term in self.SCREEN_PHRASES
        ):
            return {
                "route": "screen",
                "query": message
            }

        # ----------------------------------------------
        # WEB / CURRENT INFORMATION
        # ----------------------------------------------

        if any(
            term in text
            for term in (
                "latest ",
                "today's ",
                "todays ",
                "current news",
                "news about ",
                "on the web",
                "from the web",
                "search internet",
                "search online",
                "current version",
                "latest version",
                "latest update",
            )
        ):
            return {
                "route": "web",
                "query": self.clean_web_query(
                    message
                )
            }

        # ----------------------------------------------
        # PROJECT / CODING
        # ----------------------------------------------

        if any(
            term in text
            for term in (
                "my project",
                "this project",
                "current project",
                "project folder",
                "coding mode",
                "recent projects",
            )
        ):

            if any(
                term in text
                for term in (
                    "explain",
                    "review",
                    "code",
                    "function",
                    "class",
                    "method",
                    "source",
                    "files",
                )
            ):
                return {
                    "route": "coding",
                    "query": message
                }

            return {
                "route": "project",
                "query": message
            }

        # ----------------------------------------------
        # FILE ASSISTANT
        # ----------------------------------------------

        if any(
            term in text
            for term in (
                "my downloads",
                "my documents",
                "my files",
                "recent files",
                "downloaded file",
                "find the file",
                "find my file",
                "open file",
                "read file",
            )
        ):
            return {
                "route": "file",
                "query": message
            }

        return None

    # ==================================================
    # CLEAN WEB SEARCH QUERY
    # ==================================================

    def clean_web_query(
        self,
        message
    ):
        text = str(
            message or ""
        ).strip()

        for pattern in (
            r"^can you\s+",
            r"^please\s+",
            r"^tell me\s+",
            r"^find\s+",
            r"^look up\s+",
            r"^search\s+",
        ):
            text = re.sub(
                pattern,
                "",
                text,
                flags=re.I
            )

        return text.strip()