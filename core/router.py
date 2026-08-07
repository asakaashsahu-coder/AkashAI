from core.commands import Commands
from core.brain import Brain
from services.memory import Memory


class Router:

    def __init__(self):

        self.commands = Commands()
        self.brain = Brain()
        self.memory = Memory()

    # --------------------------------------------------
    # NORMALIZE USER MESSAGE
    # --------------------------------------------------

    def normalize_command(self, message):

        msg = message.lower().strip()

        replacements = {
            "could you": "",
            "can you": "",
            "would you": "",
            "please": "",
            "for me": "",
            "hey": "",
            "jeroo": "",
            "jaroo": "",
        }

        for old, new in replacements.items():

            msg = msg.replace(old, new)

        return " ".join(msg.split())

    # --------------------------------------------------
    # DETECT USEFUL MEMORY
    # --------------------------------------------------

    def detect_memory(self, message):

        text = message.strip()
        lower = text.lower()

        memory_patterns = [

            "my name is ",
            "i am ",
            "i'm ",
            "i use ",
            "i like ",
            "i love ",
            "i prefer ",
            "my favorite ",
            "i am learning ",
            "i'm learning ",
            "i study ",
            "i work with ",
            "i live in ",
        ]

        for pattern in memory_patterns:

            if lower.startswith(pattern):

                return text

        return None

    # --------------------------------------------------
    # MEMORY COMMANDS
    # --------------------------------------------------

    def handle_memory_command(self, message):

        normalized = self.normalize_command(
            message
        )

        # ----------------------------------------------
        # REMEMBER SOMETHING
        # ----------------------------------------------

        if normalized.startswith("remember "):

            information = normalized.replace(
                "remember ",
                "",
                1
            ).strip()

            if not information:

                return (
                    "What would you like me "
                    "to remember?"
                )

            if self.memory.add(information):

                return (
                    "🧠 Got it. I'll remember that: "
                    + information
                )

            return (
                "🧠 I already remember that."
            )

        # ----------------------------------------------
        # SHOW MEMORIES
        # ----------------------------------------------

        if normalized in [

            "what do you remember",
            "show my memories",
            "show memories",
            "my memories",

        ]:

            memories = self.memory.get_all()

            if not memories:

                return (
                    "🧠 I don't have any saved "
                    "memories yet."
                )

            return (
                "🧠 Here's what I remember:\n\n"
                + "\n".join(
                    f"• {memory}"
                    for memory in memories
                )
            )

        # ----------------------------------------------
        # CLEAR MEMORIES
        # ----------------------------------------------

        if normalized in [

            "forget everything",
            "clear memory",
            "clear memories",
            "delete my memories",

        ]:

            self.memory.clear()

            return (
                "🧹 I've cleared all "
                "saved memories."
            )

        return None

    # --------------------------------------------------
    # MAIN RESPONSE ROUTER
    # --------------------------------------------------

    def get_response(self, message):

        # ----------------------------------------------
        # MEMORY COMMANDS
        # ----------------------------------------------

        memory_command = (
            self.handle_memory_command(
                message
            )
        )

        if memory_command:

            return memory_command

        # ----------------------------------------------
        # AUTOMATIC MEMORY DETECTION
        # ----------------------------------------------

        detected_memory = (
            self.detect_memory(
                message
            )
        )

        if detected_memory:

            self.memory.add(
                detected_memory
            )

        # ----------------------------------------------
        # NORMALIZE COMMAND
        # ----------------------------------------------

        normalized = (
            self.normalize_command(
                message
            )
        )

        # ----------------------------------------------
        # LOCAL COMMANDS
        # ----------------------------------------------

        command_response = (
            self.commands.execute(
                normalized
            )
        )

        # IMPORTANT:
        # Check for None instead of truthiness.
        #
        # This means even an empty/false-like
        # command response won't accidentally
        # fall through to Gemini.

        if command_response is not None:

            return command_response

        # ----------------------------------------------
        # FIND RELEVANT MEMORIES
        # ----------------------------------------------

        relevant_memories = (
            self.memory.search(
                message
            )
        )

        # ----------------------------------------------
        # SEND MEMORY CONTEXT TO BRAIN
        # ----------------------------------------------

        if relevant_memories:

            memory_context = (
                "\n\nRelevant information I remember "
                "about the user:\n"
            )

            for memory in relevant_memories:

                memory_context += (
                    f"- {memory}\n"
                )

            message_for_brain = (
                message
                + memory_context
            )

        else:

            message_for_brain = message

        # ----------------------------------------------
        # SEND TO AI
        # ----------------------------------------------

        return self.brain.get_response(
            message_for_brain
        )