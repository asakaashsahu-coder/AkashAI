class ConversationContext:
    """Short-lived conversational context, separate from PC context and memory."""

    def __init__(self):
        self.last_user_message = None
        self.last_assistant_response = None

    def remember_exchange(self, user_message, assistant_response):
        user_message = str(user_message or "").strip()
        assistant_response = str(assistant_response or "").strip()

        if user_message:
            self.last_user_message = user_message

        if assistant_response:
            self.last_assistant_response = assistant_response

    def has_context(self):
        return bool(
            self.last_user_message
            or self.last_assistant_response
        )

    def clear(self):
        self.last_user_message = None
        self.last_assistant_response = None

    def build_followup_prompt(self, followup):
        if not self.has_context():
            return None

        return (
            "Continue the current conversation naturally.\n\n"
            "Previous user message:\n"
            f"{self.last_user_message or '(none)'}\n\n"
            "Previous assistant response:\n"
            f"{self.last_assistant_response or '(none)'}\n\n"
            "User follow-up:\n"
            f"{followup}\n\n"
            "Answer the follow-up directly and keep the same topic. "
            "Do not repeat the full previous answer unless needed."
        )
