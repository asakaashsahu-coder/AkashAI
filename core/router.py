import re
from datetime import datetime, timedelta

from core.commands import Commands
from core.brain import Brain
from core.intent_manager import IntentManager
from services.memory import Memory
from services.screen_manager import ScreenManager
from services.automation_manager import AutomationManager
from services.context_manager import ActionContext
from services.conversation_context import ConversationContext
from services.screen_context import ScreenContext
from services.screen_action_manager import ScreenActionManager
from services.coding_assistant import CodingAssistant
from services.file_assistant import FileAssistant
from services.web_research import WebResearch
from services.smart_router import SmartRouter


class Router:

    def __init__(self):
        self.commands = Commands()
        self.brain = Brain()
        self.intent_manager = IntentManager()
        self.memory = Memory()
        self.screen = ScreenManager()
        self.automation = AutomationManager()
        self.context = ActionContext()
        self.conversation_context = ConversationContext()
        self.screen_context = ScreenContext(lifetime_seconds=300)
        self.screen_actions = ScreenActionManager()
        self.coding = CodingAssistant(self.commands.projects)
        self.files = FileAssistant()
        self.web_research = WebResearch()
        self.smart_router = SmartRouter()
        self.pending_screen_action = None

        self.pending_active_close = None
        self.pending_context_close = None
        self.pending_multi_close = None
        self.pending_reminder = None

    # --------------------------------------------------
    # NORMALIZE USER MESSAGE
    # --------------------------------------------------

    def normalize_command(self, message):
        msg = message.lower().strip()

        # Speech recognition may return AM/PM as "A.M.", "a.m", etc.
        # Normalize those forms before reminder parsing.
        msg = re.sub(r"\ba\s*\.\s*m\.?\b", "am", msg, flags=re.IGNORECASE)
        msg = re.sub(r"\bp\s*\.\s*m\.?\b", "pm", msg, flags=re.IGNORECASE)

        # Remove wake-name / polite prefixes only from the beginning.
        # This avoids damaging normal words elsewhere in a sentence.
        prefix_patterns = [
            r"^(?:hey\s+)?(?:jeroo|jerro|jaroo)\b[\s,.:;!?-]*",
            r"^(?:please)\b[\s,.:;!?-]*",
            r"^(?:can you|could you|would you)\b[\s,.:;!?-]*",
        ]

        changed = True

        while changed:
            changed = False

            for pattern in prefix_patterns:
                cleaned = re.sub(
                    pattern,
                    "",
                    msg,
                    count=1,
                    flags=re.IGNORECASE
                )

                if cleaned != msg:
                    msg = cleaned.strip()
                    changed = True

        # Clean punctuation that may remain after a prefix.
        msg = re.sub(
            r"^[\s,.:;!?-]+",
            "",
            msg
        )

        # "for me" is normally a harmless trailing polite phrase.
        msg = re.sub(
            r"\s+for me[\s,.:;!?-]*$",
            "",
            msg
        )

        return " ".join(msg.split())

    # --------------------------------------------------
    # CLEAN MEMORY TEXT
    # --------------------------------------------------

    def clean_memory_text(self, text):
        text = text.strip()
        text = re.sub(r"\s+", " ", text)
        return text.rstrip(".!?")

    # --------------------------------------------------
    # DETECT USEFUL LONG-TERM MEMORY
    # --------------------------------------------------

    def detect_memory(self, message):
        text = self.clean_memory_text(message)
        lower = text.lower()

        # These patterns are intentionally limited to information that is
        # likely to still be useful in future conversations. This avoids
        # permanently storing temporary statements such as "I am tired".
        memory_patterns = [
            "my name is ",
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
            "my college is ",
            "my course is ",
            "my project is ",
        ]

        for pattern in memory_patterns:
            if lower.startswith(pattern):
                return text

        return None

    # --------------------------------------------------
    # MEMORY / CONVERSATION COMMANDS
    # --------------------------------------------------

    def handle_memory_command(self, message):
        normalized = self.normalize_command(
            message
        )

        # ----------------------------------------------
        # CLEAR CONVERSATION CONTEXT ONLY
        # ----------------------------------------------

        if normalized in [
            "clear conversation",
            "clear conversation history",
            "forget this conversation",
            "new conversation",
            "start new conversation",
        ]:
            self.brain.clear_history()

            return (
                "🧹 Conversation context cleared. "
                "Your saved long-term memories are still there."
            )

        # ----------------------------------------------
        # REMEMBER SOMETHING
        # ----------------------------------------------

        if normalized.startswith("remember "):
            information = message.strip()

            # Remove common wake/polite words without forcing the stored
            # memory to lowercase.
            information = re.sub(
                r"^(hey\s+)?(jeroo|jaroo)[,\s]*",
                "",
                information,
                flags=re.IGNORECASE
            )

            information = re.sub(
                r"^please\s+",
                "",
                information,
                flags=re.IGNORECASE
            )

            information = re.sub(
                r"^remember\s+",
                "",
                information,
                flags=re.IGNORECASE
            )

            information = self.clean_memory_text(
                information
            )

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
        # FORGET EVERYTHING
        # ----------------------------------------------

        if normalized in [
            "forget everything",
            "clear memory",
            "clear memories",
            "delete my memories",
        ]:
            self.memory.clear()

            return (
                "🧹 I've cleared all saved "
                "long-term memories."
            )

        # ----------------------------------------------
        # FORGET ONE MEMORY
        # ----------------------------------------------

        if normalized.startswith("forget "):
            information = normalized.replace(
                "forget ",
                "",
                1
            ).strip()

            if not information:
                return "What would you like me to forget?"

            result = self.memory.remove_best_match(
                information
            )

            if result is None:
                return (
                    "🧠 I couldn't find a saved memory "
                    "matching that."
                )

            if isinstance(result, list):
                return (
                    "I found more than one possible memory. "
                    "Tell me the exact one to forget:\n\n"
                    + "\n".join(
                        f"• {item}"
                        for item in result
                    )
                )

            return (
                "🧹 Forgotten: "
                + result
            )

        # ----------------------------------------------
        # SHOW MEMORIES
        # ----------------------------------------------

        if normalized in [
            "what do you remember",
            "what do you remember about me",
            "what do you know about me",
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

        return None

    # --------------------------------------------------
    # RECENT CONVERSATION HISTORY
    # --------------------------------------------------

    def handle_history_command(self, message):
        normalized = self.normalize_command(message)

        show_phrases = {
            "show our recent conversation",
            "show recent conversation",
            "show my recent conversation",
            "recent conversation",
            "show conversation history",
            "show my conversation history",
            "what did we talk about earlier",
            "what were we talking about",
            "what were we talking about earlier",
            "do you remember what we were talking about",
        }

        if normalized in show_phrases:
            history = self.brain.get_history()

            if not history:
                return "I don't have any recent conversation saved yet."

            recent = history[-10:]
            lines = []

            for item in recent:
                speaker = "You" if item.get("role") == "user" else "Jeroo"
                text = (item.get("text") or "").strip()
                if text:
                    lines.append(f"{speaker}: {text}")

            if not lines:
                return "I don't have any recent conversation saved yet."

            return "Here's our recent conversation:\n\n" + "\n\n".join(lines)

        match = re.match(
            r"^show (?:my |our )?last (\d{1,2}) (?:messages|conversation messages)$",
            normalized
        )

        if match:
            count = max(1, min(int(match.group(1)), 20))
            history = self.brain.get_history()

            if not history:
                return "I don't have any recent conversation saved yet."

            recent = history[-count:]
            lines = []

            for item in recent:
                speaker = "You" if item.get("role") == "user" else "Jeroo"
                text = (item.get("text") or "").strip()
                if text:
                    lines.append(f"{speaker}: {text}")

            return f"Here are the last {len(lines)} messages:\n\n" + "\n\n".join(lines)

        if normalized in {
            "what was my last message",
            "what did i say last",
            "what did i say before",
            "show my last message",
        }:
            history = self.brain.get_history()

            for item in reversed(history):
                if item.get("role") == "user" and item.get("text"):
                    return "Your last saved message was: " + item["text"].strip()

            return "I don't have a previous message from you saved yet."

        if normalized in {
            "what was your last message",
            "what did you say last",
            "what did you say before",
            "show your last message",
        }:
            history = self.brain.get_history()

            for item in reversed(history):
                if item.get("role") == "model" and item.get("text"):
                    return "My last saved reply was: " + item["text"].strip()

            return "I don't have a previous reply saved yet."

        if normalized in {
            "summarize our recent conversation",
            "summarise our recent conversation",
            "summarize recent conversation",
            "summarise recent conversation",
        }:
            history = self.brain.get_history()

            if not history:
                return "I don't have enough recent conversation to summarize yet."

            recent = history[-20:]
            transcript = "\n".join(
                f"{'User' if item.get('role') == 'user' else 'Jeroo'}: {item.get('text', '').strip()}"
                for item in recent
                if item.get("text")
            )

            prompt = (
                "Summarize the recent conversation below naturally and briefly. "
                "Focus on what the user and Jeroo were working on, important decisions, "
                "and the latest point reached. Do not invent anything.\n\n"
                + transcript
            )

            return self.brain.get_response(prompt, memories=None)

        return None

    # --------------------------------------------------
    # SHORT-TERM ACTION CONTEXT
    # --------------------------------------------------

    def extract_app_action(self, message):
        normalized = self.normalize_command(
            message
        )

        patterns = [
            (
                "open",
                r"^(?:open|launch|start|run)\s+(.+)$"
            ),
            (
                "close",
                r"^(?:close|quit|exit)\s+(.+)$"
            ),
            (
                "switch",
                r"^(?:switch to|focus|go to)\s+(.+)$"
            ),
        ]

        for action, pattern in patterns:
            match = re.match(
                pattern,
                normalized
            )

            if match:
                target = match.group(1).strip()

                if target:
                    return action, target

        return None, None

    def remember_local_action(self, command):
        normalized = self.normalize_command(
            command
        )

        action, target = self.extract_app_action(
            normalized
        )

        if target:
            self.context.remember_app(
                target
            )

        # Only harmless/repeatable operations are eligible for
        # "do that again". Closing apps and power commands are excluded.
        safe_prefixes = (
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

        safe_exact = {
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
        }

        if (
            normalized.startswith(safe_prefixes)
            or normalized in safe_exact
        ):
            self.context.remember_safe_command(
                normalized
            )

    def app_name_from_process(self, process):
        process = (
            process
            or ""
        ).strip().lower()

        process = re.sub(
            r"\.exe$",
            "",
            process
        )

        aliases = {
            "chrome": "chrome",
            "code": "visual studio code",
            "spotify": "spotify",
            "discord": "discord",
            "msedge": "edge",
            "notepad": "notepad",
            "calculatorapp": "calculator",
            "powershell": "powershell",
            "explorer": "file explorer",
        }

        return aliases.get(
            process,
            process
        )

    def handle_context_followup(self, message):
        normalized = self.normalize_command(
            message
        )

        # ----------------------------------------------
        # CANCEL PENDING CONTEXT / MULTI-CLOSE
        # ----------------------------------------------

        if normalized in [
            "cancel",
            "cancel that",
            "cancel close",
            "cancel closing",
            "do not close it",
            "dont close it",
            "do not close them",
            "dont close them",
        ]:
            if (
                self.pending_context_close
                or self.pending_multi_close
            ):
                self.pending_context_close = None
                self.pending_multi_close = None
                return "Okay, I cancelled the close request."

        # ----------------------------------------------
        # CONFIRM "CLOSE IT"
        # ----------------------------------------------

        if normalized in [
            "confirm close it",
            "yes close it",
            "confirm it",
        ]:
            if self.pending_context_close:
                app_name = self.pending_context_close
                self.pending_context_close = None

                return self.commands.launcher.close_app(
                    app_name
                )

        # ----------------------------------------------
        # CONFIRM MULTIPLE APP CLOSES
        # ----------------------------------------------

        if normalized in [
            "confirm close apps",
            "confirm close them",
            "yes close them",
            "close them",
        ]:
            if self.pending_multi_close:
                actions = self.pending_multi_close
                self.pending_multi_close = None

                results = []

                for action in actions:
                    response = self.commands.execute(
                        action
                    )

                    results.append(
                        response
                        or f"I couldn't run: {action}."
                    )

                return "\n".join(
                    f"• {result}"
                    for result in results
                )

        # ----------------------------------------------
        # APP PRONOUN FOLLOW-UPS
        # ----------------------------------------------

        last_app = self.context.last_app

        if normalized in [
            "close it",
            "close that",
            "close that app",
            "quit it",
            "exit it",
        ]:
            if not last_app:
                return (
                    "I don't have a recent app to refer to. "
                    "Tell me the app name first."
                )

            self.pending_context_close = last_app

            return (
                f"You mean {last_app}. "
                "Say 'confirm close it' to close it, "
                "or 'cancel' to keep it open."
            )

        if normalized in [
            "open it again",
            "reopen it",
            "open that again",
            "launch it again",
        ]:
            if not last_app:
                return (
                    "I don't have a recent app to reopen yet."
                )

            command = f"open {last_app}"

            response = self.commands.execute(
                command
            )

            if response is not None:
                self.remember_local_action(
                    command
                )

            return response

        if normalized in [
            "switch to it",
            "go to it",
            "focus it",
            "go back to it",
            "switch back to it",
        ]:
            if not last_app:
                return (
                    "I don't have a recent app to switch to yet."
                )

            command = f"switch to {last_app}"

            response = self.commands.execute(
                command
            )

            if response is not None:
                self.remember_local_action(
                    command
                )

            return response

        # ----------------------------------------------
        # REPEAT LAST SAFE PC ACTION
        # ----------------------------------------------

        if normalized in [
            "do that again",
            "do it again",
            "repeat that",
            "repeat last action",
        ]:
            command = self.context.last_safe_command

            if not command:
                return (
                    "I don't have a safe recent PC action "
                    "to repeat yet."
                )

            response = self.commands.execute(
                command
            )

            if response is not None:
                self.remember_local_action(
                    command
                )

            return response

        return None

    # --------------------------------------------------
    # CONVERSATIONAL FOLLOW-UP CONTEXT
    # --------------------------------------------------

    def is_conversation_followup(self, message):
        normalized = self.normalize_command(message)

        exact = {
            "continue", "go on", "keep going", "tell me more", "more",
            "explain more", "explain that", "explain it",
            "explain that again", "explain it again",
            "explain that simpler", "explain it simpler",
            "make it simpler", "simplify that", "simplify it",
            "give me an example", "give an example", "example",
            "another example", "give me another example",
            "why", "why is that", "how", "how so",
            "what do you mean", "what does that mean",
            "summarize that", "summarise that",
            "make it shorter", "shorter"
        }

        if normalized in exact:
            return True

        prefixes = (
            "explain that ", "explain it ", "make that ", "make it ",
            "give me an example ", "give another example ",
            "tell me more about ", "continue from ",
            "why does that ", "how does that ", "what about that "
        )

        return normalized.startswith(prefixes)

    def handle_conversation_followup(self, message):
        if not self.is_conversation_followup(message):
            return None

        prompt = self.conversation_context.build_followup_prompt(
            message
        )

        if prompt is None:
            return (
                "I don't have enough conversation context yet. "
                "Ask me something first, then use a follow-up like "
                "'explain that simpler' or 'give me an example'."
            )

        relevant_memories = self.memory.context_for(
            self.conversation_context.last_user_message or message,
            limit=8
        )

        try:
            response = self.brain.get_response(
                prompt,
                memories=relevant_memories
            )

            self.conversation_context.remember_exchange(
                message,
                response
            )

            return response

        except Exception as error:
            print(
                "Conversation follow-up error:",
                error
            )
            return None

    def remember_ai_exchange(self, user_message, response):
        if response is not None:
            self.conversation_context.remember_exchange(
                user_message,
                response
            )

    # --------------------------------------------------
    # ACTIVE WINDOW / CONTEXT COMMANDS
    # --------------------------------------------------

    def handle_active_window_command(self, message):
        normalized = self.normalize_command(message)

        if normalized in [
            "cancel close",
            "cancel closing",
            "do not close it",
            "dont close it",
        ]:
            self.pending_active_close = None
            return "Okay, I won't close it."

        if normalized in [
            "confirm close this app",
            "confirm close current app",
            "yes close this app",
            "yes close it",
        ]:
            if not self.pending_active_close:
                return "There isn't a pending app-close request."

            info = self.pending_active_close
            self.pending_active_close = None

            return self.commands.launcher.close_process(
                info.get("process"),
                display_name=info.get("title") or info.get("process")
            )

        if normalized in [
            "what app am i using",
            "what application am i using",
            "what app is this",
            "what window is active",
            "what is the active window",
            "which app is open",
            "which window am i on",
        ]:
            info = self.screen.get_active_window_info()

            if not info:
                return "I couldn't identify the active window."

            title = info.get("title") or "Untitled window"
            process = info.get("process") or "unknown process"

            app_name = self.app_name_from_process(
                process
            )

            if app_name:
                self.context.remember_app(
                    app_name
                )

            return f"You're currently on {title} ({process})."

        if normalized in [
            "close this app",
            "close current app",
            "close this window",
            "close the current app",
        ]:
            info = self.screen.get_active_window_info()

            if not info:
                return "I couldn't identify the active application."

            process = (info.get("process") or "").lower()
            title = info.get("title") or info.get("process") or "this app"

            protected = {
                "python", "pythonw", "explorer", "dwm", "system",
                "winlogon", "csrss", "services", "lsass", "svchost"
            }

            if process in protected or "jeroo" in title.lower():
                return "I won't close that because it may be Jerro or an important Windows process."

            self.pending_active_close = info

            return (
                f"The active app is {title}. "
                "Say 'confirm close this app' to close it, or 'cancel close' to keep it open."
            )

        return None

    # --------------------------------------------------
    # REMEMBERED SCREEN CONTEXT
    # --------------------------------------------------

    def is_screen_refresh_request(self, message):
        normalized = self.normalize_command(
            message
        )

        return normalized in {
            "refresh the screen",
            "refresh screen",
            "look again",
            "look at it again",
            "check the screen again",
            "analyze screen again",
            "analyse screen again",
            "analyze it again",
            "analyse it again",
            "take another look",
            "what changed",
            "what changed here",
            "what changed on screen",
            "what changed on my screen",
        }

    def is_screen_context_followup(self, message):
        normalized = self.normalize_command(
            message
        )

        if not self.screen_context.is_fresh():
            return False

        exact = {
            "what does that error mean",
            "what does the error mean",
            "explain that error",
            "why did that error happen",
            "why is that error happening",
            "how do i fix that",
            "how do i fix it",
            "how can i fix that",
            "what should i do now",
            "what should i do next",
            "what do i do next",
            "where should i click",
            "where do i click",
            "what should i click",
            "which button should i click",
            "which one should i click",
            "which line",
            "which line is wrong",
            "which line should i change",
            "show me the line",
            "explain the code on the screen",
            "explain that code",
            "what does that code do",
            "what is wrong with that code",
            "what is wrong here",
            "what is the problem here",
            "tell me more about that",
            "explain that part",
            "what does that mean",
        }

        if normalized in exact:
            return True

        phrases = [
            "that error",
            "the error",
            "that button",
            "that code",
            "which line",
            "on the screen",
            "from the screen",
            "what you saw",
            "what you just saw",
            "that window",
            "this screen",
            "that page",
        ]

        return any(
            phrase in normalized
            for phrase in phrases
        )

    def _screen_window_changed(self):
        context = self.screen_context.get()

        if not context:
            return False, None

        current_window = self.screen.get_active_window_info()

        if not current_window:
            return False, None

        changed = not self.screen_context.matches_window(
            current_window
        )

        return changed, current_window

    def handle_screen_context_followup(self, message):
        normalized = self.normalize_command(
            message
        )

        if normalized in {
            "forget the screen",
            "forget screen",
            "clear screen context",
            "clear screen memory",
        }:
            self.screen_context.clear()

            return (
                "🧹 I cleared the remembered screen context."
            )

        if self.is_screen_refresh_request(
            message
        ):
            return self.analyze_screen_change(
                message
            )

        if not self.is_screen_context_followup(
            message
        ):
            return None

        context = self.screen_context.get()

        if not context:
            return None

        changed, current_window = self._screen_window_changed()

        if changed:
            title = (
                current_window.get("title")
                if current_window
                else ""
            )

            return self.analyze_screen(
                (
                    f"{message}\n\n"
                    "The foreground window changed since the previous "
                    "screen analysis. Analyze what is visible now instead "
                    "of relying on the old screen context."
                    + (
                        f" The current window is '{title}'."
                        if title
                        else ""
                    )
                )
            )

        prompt = (
            "The user is asking a follow-up about a screen you analyzed "
            "recently. The foreground window is still the same. Use the "
            "remembered analysis below and answer naturally. Do not claim "
            "you are looking at a new screenshot. If precise visual details "
            "may have changed inside the same window, recommend 'look again'.\n\n"
            "Previous screen-analysis request:\n"
            f"{context.get('original_request') or '(not recorded)'}\n\n"
            "Analysis mode:\n"
            f"{context.get('analysis_mode') or 'general'}\n\n"
            "Remembered screen analysis:\n"
            f"{context.get('analysis')}\n\n"
            "Foreground window:\n"
            f"{context.get('window_title') or 'Unknown'} "
            f"({context.get('app_name') or context.get('process_name') or 'unknown app'})\n\n"
            "User follow-up:\n"
            f"{message}\n\n"
            "Answer the follow-up directly. For coding errors, mention the "
            "likely line or visible code area when the remembered analysis "
            "supports it. For click guidance, describe the visible control "
            "clearly instead of inventing coordinates."
        )

        relevant_memories = self.memory.context_for(
            message,
            limit=5
        )

        response = self.brain.get_response(
            prompt,
            memories=relevant_memories
        )

        self.conversation_context.remember_exchange(
            message,
            response
        )

        return response

    # --------------------------------------------------
    # SCREEN -> SAFE ACTION
    # --------------------------------------------------

    def is_screen_action_request(self, message):
        normalized = self.normalize_command(
            message
        )

        exact = {
            "do the next step",
            "do that for me",
            "can you do that",
            "do it for me",
            "take the next step",
            "perform the next step",
            "fix it for me",
            "do the safe action",
            "do the suggested action",
            "perform that action",
        }

        if normalized in exact:
            return True

        phrases = (
            "based on the screen",
            "based on what you saw",
            "from what you saw",
            "do the next step",
            "can you do it",
            "do that for me",
        )

        return any(
            phrase in normalized
            for phrase in phrases
        )

    def plan_screen_action(self, message):
        context = self.screen_context.get()

        if not context:
            return (
                "I don't have a recent screen analysis to act from. "
                "Ask me to look at the screen first."
            )

        safe_command = self.screen_actions.plan(
            self.brain,
            context,
            message
        )

        if not safe_command:
            return (
                "I can explain the next step, but I don't have a safe "
                "supported PC action for that yet."
            )

        self.pending_screen_action = safe_command

        return (
            f"From the screen context, I can run: '{safe_command}'. "
            "Say 'confirm screen action' to run it, or 'cancel' to stop."
        )

    def handle_pending_screen_action(self, message):
        normalized = self.normalize_command(
            message
        )

        if normalized in {
            "cancel",
            "cancel that",
            "cancel screen action",
            "do not do it",
            "dont do it",
        }:
            if self.pending_screen_action:
                self.pending_screen_action = None

                return (
                    "Okay, I cancelled the screen action."
                )

        if normalized in {
            "confirm screen action",
            "confirm that action",
            "confirm action",
            "yes do it",
            "yes",
            "do it",
            "go ahead",
        }:
            if not self.pending_screen_action:
                return (
                    "There isn't a pending screen action to confirm."
                )

            command = self.pending_screen_action
            self.pending_screen_action = None

            response = self.commands.execute(
                command
            )

            if response is None:
                return (
                    f"I couldn't run the planned action: {command}."
                )

            self.remember_local_action(
                command
            )

            return response

        return None

    # --------------------------------------------------
    # SCREEN-AWARE REQUEST DETECTION
    # --------------------------------------------------

    def screen_analysis_mode(self, message, active_window=None):
        normalized = self.normalize_command(
            message
        )

        if any(
            phrase in normalized
            for phrase in (
                "error",
                "not working",
                "failed",
                "exception",
                "traceback",
                "bug",
                "fix this",
            )
        ):
            return "error"

        if any(
            phrase in normalized
            for phrase in (
                "summarize",
                "summarise",
                "summary",
                "read this page",
                "explain this page",
            )
        ):
            return "summary"

        if any(
            phrase in normalized
            for phrase in (
                "what should i click",
                "where should i click",
                "what do i click",
                "which button",
            )
        ):
            return "click_guidance"

        if any(
            phrase in normalized
            for phrase in (
                "code",
                "which line",
                "function",
                "class",
            )
        ):
            return "code"

        if active_window:
            app_type = active_window.get(
                "app_type"
            )

            if app_type == "code_editor":
                return "code"

            if app_type == "terminal":
                return "error"

            if app_type == "browser":
                return "webpage"

        return "general"

    def build_screen_instruction(
        self,
        message,
        active_window=None,
        previous_analysis=None
    ):
        mode = self.screen_analysis_mode(
            message,
            active_window
        )

        app_name = "Unknown app"
        title = "Unknown window"
        app_type = "general"

        if active_window:
            app_name = (
                active_window.get("app_name")
                or active_window.get("process")
                or app_name
            )
            title = (
                active_window.get("title")
                or title
            )
            app_type = (
                active_window.get("app_type")
                or app_type
            )

        instruction = (
            f"\n\nJerro v1.5 screen mode: {mode}.\n"
            f"Active app: {app_name}.\n"
            f"Window title: {title}.\n"
            f"App type: {app_type}.\n\n"
            "Analyze only what is actually visible in the screenshot. "
            "Be practical and specific. Do not invent text, buttons, code "
            "lines, errors, or UI elements that cannot be seen. "
        )

        if mode == "error":
            instruction += (
                "Focus on the visible error. Explain what failed, the likely "
                "cause, the visible clue supporting it, and the safest next "
                "fix to try. If code or a traceback is visible, mention the "
                "file or line only when readable."
            )

        elif mode == "code":
            instruction += (
                "Treat this as a coding workspace. Identify the language or "
                "file when visible, explain the relevant code, point out "
                "visible mistakes, and give a concrete next change. Avoid "
                "rewriting unrelated code."
            )

        elif mode in {
            "summary",
            "webpage"
        }:
            instruction += (
                "Give a compact summary of the visible page first, then "
                "mention the most important details or actions. Distinguish "
                "visible page content from browser navigation."
            )

        elif mode == "click_guidance":
            instruction += (
                "Identify the visible control the user should use and "
                "describe it by label, icon, and nearby UI context. Do not "
                "claim pixel-perfect coordinates. If the action is unclear "
                "or risky, say so instead of guessing."
            )

        else:
            instruction += (
                "Start with what the user is looking at, then explain the "
                "most useful visible details and the likely next step."
            )

        if previous_analysis:
            instruction += (
                "\n\nPrevious screen analysis:\n"
                f"{previous_analysis}\n\n"
                "Compare the new screenshot with that previous analysis. "
                "Mention only meaningful changes supported by the new screen."
            )

        return instruction, mode

    def is_screen_request(self, message):
        normalized = self.normalize_command(
            message
        )

        exact_phrases = [
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
            "summarize this page",
            "summarise this page",
            "summarize this screen",
            "summarise this screen",
            "explain this page",
            "read this page",
        ]

        if normalized in exact_phrases:
            return True

        screen_words = [
            "screen",
            "on screen",
            "on my display",
            "this page",
        ]

        action_words = [
            "look",
            "analyze",
            "analyse",
            "explain",
            "read",
            "describe",
            "check",
            "see",
            "error",
            "click",
            "help",
            "what",
            "summarize",
            "summarise",
        ]

        if any(
            word in normalized
            for word in screen_words
        ):
            return any(
                word in normalized
                for word in action_words
            )

        contextual_phrases = [
            "explain this error",
            "what does this error mean",
            "what should i click",
            "where should i click",
            "what do i click",
            "help me with this",
            "help with this",
            "explain this",
            "fix this",
            "why is this not working",
            "what is this",
        ]

        return any(
            phrase in normalized
            for phrase in contextual_phrases
        )

    # --------------------------------------------------
    # ANALYZE CURRENT SCREEN
    # --------------------------------------------------

    def analyze_screen(self, message):
        image_bytes, error = self.screen.capture_screen_bytes()

        if error:
            return error

        relevant_memories = self.memory.context_for(
            message,
            limit=5
        )

        active_window = self.screen.get_active_window_info()

        instruction, mode = self.build_screen_instruction(
            message,
            active_window
        )

        screen_message = (
            f"{message}"
            f"{instruction}"
        )

        response = self.brain.get_screen_response(
            screen_message,
            image_bytes,
            memories=relevant_memories
        )

        if response:
            active_window = active_window or {}

            self.screen_context.remember(
                analysis=response,
                original_request=message,
                window_title=active_window.get(
                    "title"
                ),
                process_name=active_window.get(
                    "process"
                ),
                app_name=active_window.get(
                    "app_name"
                ),
                app_type=active_window.get(
                    "app_type"
                ),
                analysis_mode=mode
            )

            self.conversation_context.remember_exchange(
                message,
                response
            )

        return response

    def analyze_screen_change(self, message):
        previous = self.screen_context.get()
        previous_analysis = (
            previous.get("analysis")
            if previous
            else None
        )

        image_bytes, error = self.screen.capture_screen_bytes()

        if error:
            return error

        active_window = self.screen.get_active_window_info()

        instruction, mode = self.build_screen_instruction(
            message,
            active_window,
            previous_analysis=previous_analysis
        )

        screen_message = (
            "The user asked you to look again at the current screen and "
            "identify what changed or what matters now.\n\n"
            f"User request: {message}"
            f"{instruction}"
        )

        response = self.brain.get_screen_response(
            screen_message,
            image_bytes,
            memories=self.memory.context_for(
                message,
                limit=5
            )
        )

        if response:
            active_window = active_window or {}

            self.screen_context.remember(
                analysis=response,
                original_request=message,
                window_title=active_window.get(
                    "title"
                ),
                process_name=active_window.get(
                    "process"
                ),
                app_name=active_window.get(
                    "app_name"
                ),
                app_type=active_window.get(
                    "app_type"
                ),
                analysis_mode=mode
            )

            self.conversation_context.remember_exchange(
                message,
                response
            )

        return response


    # --------------------------------------------------
    # CUSTOM ROUTINES
    # --------------------------------------------------

    def parse_routine_actions(self, action_text):
        text = self.normalize_command(
            action_text
        )

        if not text:
            return []

        action_verbs = (
            "open ", "launch ", "start ", "run ",
            "close ", "quit ", "exit ",
            "switch to ", "focus ", "go to ",
            "search google ", "search google for ",
            "search youtube ", "search youtube for ",
            "volume up", "volume down", "mute",
            "take a screenshot"
        )

        # First support the same shorthand as multi-action commands:
        # "open chrome and spotify"
        inherited = self.split_multi_action(text)

        if inherited:
            return inherited

        # For richer routines:
        # "open chrome, open spotify, then open vs code"
        parts = re.split(
            r"\s*(?:;|,|\band then\b|\bthen\b|\band(?=\s+"
            r"(?:open|launch|start|run|close|quit|exit|"
            r"switch to|focus|go to|search google|"
            r"search youtube|volume|mute|take)))\s*",
            text
        )

        actions = [
            part.strip()
            for part in parts
            if part.strip()
        ]

        if len(actions) == 1:
            return actions

        valid = []

        for action in actions:
            if action.startswith(action_verbs):
                valid.append(action)
            else:
                return []

        return valid

    def execute_routine(self, name):
        actions = self.automation.get_routine(
            name
        )

        if actions is None:
            return None

        results = []

        for action in actions:
            response = self.commands.execute(
                action
            )

            if response is None:
                results.append(
                    f"I couldn't run: {action}."
                )
            else:
                results.append(response)

        return (
            f"⚙️ Routine '{name}' finished:\n"
            + "\n".join(
                f"• {result}"
                for result in results
            )
        )

    def handle_routine_command(self, message):
        normalized = self.normalize_command(
            message
        )

        if normalized in [
            "show routines",
            "show my routines",
            "list routines",
            "list my routines",
            "what routines do i have",
        ]:
            return self.automation.list_routines()

        create_match = re.match(
            r"^(?:create|make|save)\s+(?:a\s+)?routine\s+"
            r"(.+?)\s+(?:with|that does)\s+(.+)$",
            normalized
        )

        if create_match:
            name = create_match.group(1).strip()
            action_text = create_match.group(2).strip()

            actions = self.parse_routine_actions(
                action_text
            )

            if not actions:
                return (
                    "I couldn't understand the routine actions. "
                    "Try: create routine coding mode with "
                    "open VS Code and Chrome"
                )

            return self.automation.save_routine(
                name,
                actions
            )

        delete_match = re.match(
            r"^(?:delete|remove)\s+(?:my\s+)?routine\s+(.+)$",
            normalized
        )

        if delete_match:
            return self.automation.delete_routine(
                delete_match.group(1)
            )

        show_match = re.match(
            r"^(?:show|describe)\s+(?:my\s+)?routine\s+(.+)$",
            normalized
        )

        if show_match:
            return self.automation.describe_routine(
                show_match.group(1)
            )

        explicit_run = re.match(
            r"^(?:run|start|activate)\s+(?:my\s+)?routine\s+(.+)$",
            normalized
        )

        if explicit_run:
            name = explicit_run.group(1).strip()

            result = self.execute_routine(
                name
            )

            if result is None:
                return (
                    f"I couldn't find a routine "
                    f"called '{name}'."
                )

            return result

        # Natural shortcut:
        # "start coding mode" / "run coding mode"
        natural_run = re.match(
            r"^(?:run|start|activate)\s+(.+)$",
            normalized
        )

        if natural_run:
            name = natural_run.group(1).strip()

            if self.automation.routine_exists(
                name
            ):
                return self.execute_routine(
                    name
                )

        # Also allow just:
        # "coding mode"
        if normalized.endswith(" mode"):
            if self.automation.routine_exists(
                normalized
            ):
                return self.execute_routine(
                    normalized
                )

        return None


    # --------------------------------------------------
    # NOTES / REMINDERS / MULTI-ACTION AUTOMATION
    # --------------------------------------------------

    def _build_reminder_datetime(
        self,
        hour_text,
        minute_text=None,
        meridiem=None,
        tomorrow=False
    ):
        try:
            hour = int(
                hour_text
            )
            minute = int(
                minute_text or 0
            )
        except (TypeError, ValueError):
            return None

        if minute < 0 or minute > 59:
            return None

        meridiem = (
            meridiem
            or ""
        ).lower().strip()

        if meridiem:
            if hour < 1 or hour > 12:
                return None

            if meridiem == "am":
                hour = (
                    0
                    if hour == 12
                    else hour
                )
            else:
                hour = (
                    12
                    if hour == 12
                    else hour + 12
                )
        elif hour < 0 or hour > 23:
            return None

        now = datetime.now()

        due = now.replace(
            hour=hour,
            minute=minute,
            second=0,
            microsecond=0
        )

        if tomorrow:
            due += timedelta(
                days=1
            )
        elif due <= now:
            due += timedelta(
                days=1
            )

        return due

    def _nearest_future_time(self, hour_text, minute_text=None, meridiem=None, tomorrow=False):
        """Build a reminder datetime, treating bare 1-12 hours like normal speech."""
        try:
            hour = int(hour_text)
            minute = int(minute_text or 0)
        except (TypeError, ValueError):
            return None

        if minute < 0 or minute > 59:
            return None

        if meridiem:
            return self._build_reminder_datetime(
                str(hour),
                str(minute),
                meridiem,
                tomorrow=tomorrow
            )

        # A bare hour such as "at 6" is normally conversational 12-hour time.
        # Pick the nearest future 6 AM / 6 PM instead of always assuming 06:00.
        if 1 <= hour <= 12:
            now = datetime.now()
            candidates = []

            for suffix in ("am", "pm"):
                candidate = self._build_reminder_datetime(
                    str(hour),
                    str(minute),
                    suffix,
                    tomorrow=tomorrow
                )

                if candidate is not None:
                    candidates.append(candidate)

            if candidates:
                return min(candidates)

        return self._build_reminder_datetime(
            str(hour),
            str(minute),
            None,
            tomorrow=tomorrow
        )

    def _daypart_time(self, daypart, daily=False):
        """Return a practical default time for common daily-life phrases."""
        defaults = {
            "morning": (8, 0),
            "after breakfast": (9, 0),
            "noon": (12, 0),
            "lunch": (13, 0),
            "after lunch": (14, 0),
            "afternoon": (15, 0),
            "evening": (19, 0),
            "tonight": (20, 0),
            "night": (21, 0),
            "bedtime": (23, 0),
        }

        if daypart not in defaults:
            return None

        hour, minute = defaults[daypart]
        now = datetime.now()
        due = now.replace(
            hour=hour,
            minute=minute,
            second=0,
            microsecond=0
        )

        if due <= now:
            due += timedelta(days=1)

        return due

    def _set_pending_reminder(self, task=None, due=None, daily=False):
        self.pending_reminder = {
            "task": (task or "").strip(),
            "due": due,
            "daily": bool(daily),
        }

    def _finish_pending_reminder(self, message):
        pending = self.pending_reminder

        if not pending:
            return None

        normalized = self.normalize_command(message)
        task = pending.get("task", "").strip()
        due = pending.get("due")
        daily = pending.get("daily", False)

        if due is None:
            # Follow-ups such as "at 8 tonight", "tomorrow at 7", or "in 20 minutes".
            relative = re.match(
                r"^(?:in\s+)?"
                r"(half an hour|an hour|\d+\s*(?:minutes?|mins?|hours?|hrs?))$",
                normalized
            )

            if relative:
                value = relative.group(1)

                if value == "half an hour":
                    minutes = 30
                elif value == "an hour":
                    minutes = 60
                else:
                    match = re.match(
                        r"(\d+)\s*(minutes?|mins?|hours?|hrs?)",
                        value
                    )
                    amount = int(match.group(1))
                    unit = match.group(2)
                    minutes = (
                        amount * 60
                        if unit.startswith(("hour", "hr"))
                        else amount
                    )

                self.pending_reminder = None
                return self.automation.add_reminder(task, minutes)

            follow_time = re.match(
                r"^(?:(today|tomorrow)\s+)?(?:at\s+)?"
                r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?"
                r"(?:\s+(tonight|today|tomorrow))?$",
                normalized
            )

            if follow_time:
                tomorrow = (
                    follow_time.group(1) == "tomorrow"
                    or follow_time.group(5) == "tomorrow"
                )
                due = self._nearest_future_time(
                    follow_time.group(2),
                    follow_time.group(3),
                    follow_time.group(4),
                    tomorrow=tomorrow
                )

            if due is None:
                for daypart in (
                    "after breakfast", "after lunch", "morning", "noon",
                    "afternoon", "evening", "tonight", "night", "bedtime"
                ):
                    if normalized == daypart or normalized == f"in the {daypart}":
                        due = self._daypart_time(daypart, daily=daily)
                        break

            if due is None:
                return "What time should I use for that reminder?"

        if not task:
            cleaned = normalized
            cleaned = re.sub(r"^(?:to\s+|about\s+)", "", cleaned).strip()

            if not cleaned:
                return "What should I remind you about?"

            task = cleaned

        self.pending_reminder = None

        if daily:
            return self.automation.add_daily_reminder(task, due)

        return self.automation.add_reminder_at(task, due)

    def handle_automation_command(self, message):
        normalized = self.normalize_command(message)

        # Complete a conversational reminder that was missing either the
        # time or task. A fresh "remind me..." command starts a new reminder
        # instead of being consumed by stale pending state.
        fresh_reminder = (
            normalized.startswith("remind me")
            or normalized.startswith("set a reminder")
            or normalized.startswith("set reminder")
            or normalized.startswith("create a reminder")
        )

        if fresh_reminder and self.pending_reminder is not None:
            self.pending_reminder = None
        else:
            pending_result = self._finish_pending_reminder(message)
            if pending_result is not None:
                return pending_result

        note_prefixes = [
            "create a note saying ",
            "create note saying ",
            "make a note saying ",
            "note that ",
            "save a note saying ",
        ]

        for prefix in note_prefixes:
            if normalized.startswith(prefix):
                note = normalized[len(prefix):].strip()
                return self.automation.add_note(note)

        if normalized in [
            "show my notes", "show notes",
            "list my notes", "list notes",
        ]:
            return self.automation.list_notes()

        if normalized in [
            "clear my notes", "clear notes",
            "delete all notes",
        ]:
            return self.automation.clear_notes()

        # Relative reminders:
        # "Remind me in 20 minutes to check the food"
        # "Remind me in 1 min to test notification"
        # "Remind me in 2 hrs to call him"
        reminder = re.match(
            r"^remind me in\s+(\d+)\s*"
            r"(minutes?|mins?|hours?|hrs?)"
            r"(?:\s+to\s+(.+))?$",
            normalized
        )

        if reminder:
            amount = int(reminder.group(1))
            unit = reminder.group(2)
            task = (
                reminder.group(3).strip()
                if reminder.group(3)
                else ""
            )

            minutes = (
                amount * 60
                if unit.startswith(("hour", "hr"))
                else amount
            )

            if not task:
                due = datetime.now() + timedelta(
                    minutes=minutes
                )
                self._set_pending_reminder(
                    due=due
                )
                return "Sure. What should I remind you about?"

            return self.automation.add_reminder(
                task,
                minutes
            )

        # "In half an hour remind me to check the food"
        half_hour = re.match(
            r"^in\s+half an hour\s+remind me(?:\s+to)?\s+(.+)$",
            normalized
        )

        if half_hour:
            return self.automation.add_reminder(
                half_hour.group(1).strip(),
                30
            )

        # "Remind me in half an hour [to check the food]"
        half_hour_alt = re.match(
            r"^remind me in\s+half an hour"
            r"(?:\s+to\s+(.+))?$",
            normalized
        )

        if half_hour_alt:
            task = (
                half_hour_alt.group(1).strip()
                if half_hour_alt.group(1)
                else ""
            )

            if not task:
                self._set_pending_reminder(
                    due=datetime.now() + timedelta(
                        minutes=30
                    )
                )
                return "Sure. What should I remind you about?"

            return self.automation.add_reminder(
                task,
                30
            )

        # "Remind me at 9 PM to take medicine"
        exact_reminder = re.match(
            r"^remind me at\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\s+to\s+(.+)$",
            normalized
        )

        if exact_reminder:
            due = self._nearest_future_time(
                exact_reminder.group(1),
                exact_reminder.group(2),
                exact_reminder.group(3)
            )

            if due is None:
                return "I couldn't understand that reminder time."

            return self.automation.add_reminder_at(
                exact_reminder.group(4).strip(),
                due
            )

        # "Remind me to drink water at 10 AM"
        task_first = re.match(
            r"^remind me to\s+(.+?)\s+at\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?$",
            normalized
        )

        if task_first:
            due = self._nearest_future_time(
                task_first.group(2),
                task_first.group(3),
                task_first.group(4)
            )

            if due is None:
                return "I couldn't understand that reminder time."

            return self.automation.add_reminder_at(
                task_first.group(1).strip(),
                due
            )

        # "Remind me tomorrow at 7 AM to wake up"
        tomorrow_reminder = re.match(
            r"^remind me tomorrow at\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\s+to\s+(.+)$",
            normalized
        )

        if tomorrow_reminder:
            due = self._nearest_future_time(
                tomorrow_reminder.group(1),
                tomorrow_reminder.group(2),
                tomorrow_reminder.group(3),
                tomorrow=True
            )

            if due is None:
                return "I couldn't understand that reminder time."

            return self.automation.add_reminder_at(
                tomorrow_reminder.group(4).strip(),
                due
            )

        # "Wake me up tomorrow at 7"
        wake_up = re.match(
            r"^wake me up(?:\s+tomorrow)?\s+at\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?$",
            normalized
        )

        if wake_up:
            due = self._nearest_future_time(
                wake_up.group(1),
                wake_up.group(2),
                wake_up.group(3),
                tomorrow="tomorrow" in normalized
            )

            if due is None:
                return "I couldn't understand that wake-up time."

            return self.automation.add_reminder_at("wake up", due)

        # "At 6 remind me I have class" / "At 10 tell me to stop using the laptop"
        time_first = re.match(
            r"^at\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\s+"
            r"(?:remind me(?:\s+to)?|tell me to)\s+(.+)$",
            normalized
        )

        if time_first:
            due = self._nearest_future_time(
                time_first.group(1),
                time_first.group(2),
                time_first.group(3)
            )

            if due is None:
                return "I couldn't understand that reminder time."

            return self.automation.add_reminder_at(
                time_first.group(4).strip(),
                due
            )

        # Daily reminders with an exact time.
        daily_exact = re.match(
            r"^remind me\s+(?:every day|everyday|daily)\s+at\s+"
            r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\s+to\s+(.+)$",
            normalized
        )

        if daily_exact:
            due = self._nearest_future_time(
                daily_exact.group(1),
                daily_exact.group(2),
                daily_exact.group(3)
            )

            if due is None:
                return "I couldn't understand that daily reminder time."

            return self.automation.add_daily_reminder(
                daily_exact.group(4).strip(),
                due
            )

        daily_exact_alt = re.match(
            r"^(?:every day|everyday|daily)\s+(?:at\s+)?"
            r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\s+"
            r"remind me(?:\s+to)?\s+(.+)$",
            normalized
        )

        if daily_exact_alt:
            due = self._nearest_future_time(
                daily_exact_alt.group(1),
                daily_exact_alt.group(2),
                daily_exact_alt.group(3)
            )

            if due is None:
                return "I couldn't understand that daily reminder time."

            return self.automation.add_daily_reminder(
                daily_exact_alt.group(4).strip(),
                due
            )

        # "Every morning remind me to drink water"
        daypart_daily = re.match(
            r"^every\s+(morning|afternoon|evening|night)\s+"
            r"remind me(?:\s+to)?\s+(.+)$",
            normalized
        )

        if daypart_daily:
            daypart = daypart_daily.group(1)
            due = self._daypart_time(daypart, daily=True)

            return self.automation.add_daily_reminder(
                daypart_daily.group(2).strip(),
                due
            )

        # "Remind me every morning to drink water"
        daypart_daily_alt = re.match(
            r"^remind me every\s+(morning|afternoon|evening|night)\s+to\s+(.+)$",
            normalized
        )

        if daypart_daily_alt:
            daypart = daypart_daily_alt.group(1)
            due = self._daypart_time(daypart, daily=True)

            return self.automation.add_daily_reminder(
                daypart_daily_alt.group(2).strip(),
                due
            )

        # "Remind me after lunch to work on coding"
        daypart_once = re.match(
            r"^remind me\s+(after breakfast|after lunch|morning|afternoon|evening|tonight|at night|at bedtime)\s+to\s+(.+)$",
            normalized
        )

        if daypart_once:
            daypart = daypart_once.group(1)
            daypart = daypart.replace("at ", "", 1) if daypart.startswith("at ") else daypart
            due = self._daypart_time(daypart)

            return self.automation.add_reminder_at(
                daypart_once.group(2).strip(),
                due
            )

        # Natural "I need to call him tonight, remind me" style.
        need_reminder = re.match(
            r"^i need to\s+(.+?)\s+(tonight|this evening|tomorrow morning|tomorrow),?\s+remind me$",
            normalized
        )

        if need_reminder:
            task = need_reminder.group(1).strip()
            when = need_reminder.group(2)

            if when == "tonight":
                due = self._daypart_time("tonight")
            elif when == "this evening":
                due = self._daypart_time("evening")
            elif when == "tomorrow morning":
                now = datetime.now()
                due = (now + timedelta(days=1)).replace(
                    hour=8, minute=0, second=0, microsecond=0
                )
            else:
                # Tomorrow without a time is ambiguous, so ask naturally.
                self._set_pending_reminder(task=task)
                return "Sure. What time tomorrow should I remind you?"

            return self.automation.add_reminder_at(task, due)

        # Missing task: "Remind me at 8:55 AM"
        missing_task = re.match(
            r"^remind me at\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?$",
            normalized
        )

        if missing_task:
            due = self._nearest_future_time(
                missing_task.group(1),
                missing_task.group(2),
                missing_task.group(3)
            )

            if due is None:
                return "I couldn't understand that reminder time."

            self._set_pending_reminder(due=due)
            return "Sure. What should I remind you about?"

        # Missing time: "Remind me to study"
        missing_time = re.match(
            r"^remind me(?:\s+to)?\s+(.+)$",
            normalized
        )

        if missing_time:
            task = missing_time.group(1).strip()

            if task:
                self._set_pending_reminder(task=task)
                return "Sure. When should I remind you?"

        if normalized in [
            "what do i have today",
            "what's on my schedule today",
            "whats on my schedule today",
            "today's reminders",
            "todays reminders",
            "give me my daily brief",
            "give me my daily briefing",
        ]:
            return self.automation.today_summary()

        if normalized in [
            "show reminders", "show my reminders",
            "list reminders", "list my reminders",
        ]:
            return self.automation.list_reminders()

        if normalized in [
            "clear reminders", "clear my reminders",
            "delete all reminders",
        ]:
            return self.automation.clear_reminders()

        return None

    def split_multi_action(self, message):
        normalized = self.normalize_command(message)

        action_verbs = (
            "open ", "launch ", "start ", "run ",
            "close ", "quit ", "exit ",
            "switch to ", "focus ", "go to ",
            "search google ", "search google for ",
            "search youtube ", "search youtube for "
        )

        matched_verb = None

        for verb in action_verbs:
            if normalized.startswith(verb):
                matched_verb = verb
                break

        if not matched_verb:
            return None

        if not re.search(
            r"\s+(?:and then|then|and)\s+",
            normalized
        ):
            return None

        parts = [
            part.strip()
            for part in re.split(
                r"\s+(?:and then|then|and)\s+",
                normalized
            )
            if part.strip()
        ]

        if len(parts) < 2 or len(parts) > 6:
            return None

        actions = [parts[0]]

        for part in parts[1:]:
            if part.startswith(action_verbs):
                actions.append(part)
            else:
                actions.append(matched_verb + part)

        return actions

    def run_multi_action(self, message):
        actions = self.split_multi_action(
            message
        )

        if not actions:
            return None

        # Closing several applications at once gets an extra confirmation.
        close_actions = [
            action
            for action in actions
            if action.startswith(
                ("close ", "quit ", "exit ")
            )
        ]

        if len(close_actions) >= 2:
            self.pending_multi_close = close_actions

            names = []

            for action in close_actions:
                _, target = self.extract_app_action(
                    action
                )

                if target:
                    names.append(target)

            return (
                "You're asking me to close multiple apps"
                + (
                    ": " + ", ".join(names)
                    if names
                    else ""
                )
                + ". Say 'confirm close apps' to continue, "
                "or 'cancel' to stop."
            )

        results = []

        for action in actions:
            response = self.commands.execute(
                action
            )

            if response is None:
                results.append(
                    f"I couldn't run: {action}."
                )
            else:
                results.append(
                    response
                )

                self.remember_local_action(
                    action
                )

        return "\n".join(
            f"• {result}"
            for result in results
        )

    # --------------------------------------------------
    # SMART NATURAL-LANGUAGE ROUTING
    # --------------------------------------------------

    def smart_route_request(self, message):
        decision = self.smart_router.rule_route(message)

        if decision is None:
            return None

        route = decision.get("route")
        query = decision.get("query") or message

        if route == "screen":
            return self.analyze_screen(query)

        if route == "web":
            results = self.web_research.search(query, limit=6)

            if not results:
                return "I couldn't reach web search right now."

            prompt = self.web_research.build_research_prompt(
                query,
                results
            )

            response = self.brain.get_response(
                prompt,
                memories=None
            )

            self.remember_ai_exchange(
                message,
                response
            )

            return response

        if route == "file":
            return self.handle_file_command(message)

        if route == "coding":
            return self.handle_coding_command(message)

        if route == "project":
            return self.handle_project_command(message)

        return None

    # --------------------------------------------------
    # WEB RESEARCH
    # --------------------------------------------------

    def handle_web_research(self, message):
        normalized = self.normalize_command(message)

        prefixes = (
            "search the web for ",
            "search web for ",
            "web search ",
            "research ",
            "look up ",
            "lookup ",
            "find online ",
        )

        query = None

        for prefix in prefixes:
            if normalized.startswith(prefix):
                query = message[len(prefix):].strip()
                break

        if not query:
            return None

        if not query:
            return "Tell me what you want me to research."

        results = self.web_research.search(
            query,
            limit=6
        )

        if not results:
            return (
                "I couldn't reach web search right now. "
                "Check the internet connection and try again."
            )

        prompt = self.web_research.build_research_prompt(
            query,
            results
        )

        response = self.brain.get_response(
            prompt,
            memories=None
        )

        self.remember_ai_exchange(
            message,
            response
        )

        return response

    def is_web_research_request(self, message):
        normalized = self.normalize_command(message)

        return normalized.startswith((
            "search the web for ",
            "search web for ",
            "web search ",
            "research ",
            "look up ",
            "lookup ",
            "find online ",
        ))

    # --------------------------------------------------
    # LOCAL FILE ASSISTANT
    # --------------------------------------------------

    def handle_file_command(self, message):
        normalized = self.normalize_command(message)

        if normalized in {
            "show recent files",
            "show my recent files",
            "recent files",
            "files from today",
            "show files from today",
        }:
            results = self.files.recent_files(
                hours=24
            )

            return self.files.format_results(
                results,
                "Recent files"
            )

        match = re.match(
            r"^(?:find|search for|locate)\s+(?:my\s+)?(.+?)(?:\s+file)?$",
            normalized
        )

        if match:
            query = match.group(1).strip()

            # Avoid stealing coding-symbol searches.
            if not query.startswith(
                ("function ", "class ", "method ", "symbol ")
            ):
                results = self.files.find_files(query)

                return self.files.format_results(
                    results,
                    f"Matches for '{query}'"
                )

        match = re.match(
            r"^(?:open|read)\s+(?:file\s+)?(?:number\s+)?(\d+)$",
            normalized
        )

        if match:
            path = self.files.resolve_last_result(
                match.group(1)
            )

            if not path:
                return (
                    "I don't have that numbered file in the "
                    "current search results."
                )

            if normalized.startswith("open"):
                return self.files.open_path(path)

            text, error = self.files.read_path(path)

            if error:
                return error

            prompt = (
                f"Summarize this local file for the user.\n\n"
                f"File: {path.name}\n\n{text}"
            )

            response = self.brain.get_response(
                prompt,
                memories=None
            )

            self.remember_ai_exchange(
                message,
                response
            )

            return response

        return None

    def is_file_request(self, message):
        normalized = self.normalize_command(message)

        return (
            normalized in {
                "show recent files",
                "show my recent files",
                "recent files",
                "files from today",
                "show files from today",
            }
            or normalized.startswith(
                ("find ", "search for ", "locate ", "open file ", "read file ")
            )
            or bool(
                re.match(r"^(?:open|read)\s+(?:number\s+)?\d+$", normalized)
            )
        )

    # --------------------------------------------------
    # CODING ASSISTANT
    # --------------------------------------------------

    def handle_coding_command(self, message):
        normalized = self.normalize_command(message)

        if normalized in {
            "show project files",
            "show source files",
            "list project files",
            "list source files",
        }:
            files, error = self.coding.list_files()

            if error:
                return error

            return (
                "📄 Active project files:\n\n"
                + "\n".join(f"• {name}" for name in files)
            )

        match = re.match(
            r"^(?:find|locate|search for)\s+"
            r"(?:function|class|method|symbol|text)?\s*(.+)$",
            normalized
        )

        if match and " file" not in normalized:
            term = match.group(1).strip()
            matches, error = self.coding.search_symbol(term)

            if error:
                return error

            if not matches:
                return f"I couldn't find '{term}' in the active project."

            return (
                f"🔎 Matches for '{term}':\n\n"
                + "\n".join(
                    f"• {item['file']}:{item['line']} — {item['text']}"
                    for item in matches
                )
            )

        match = re.search(
            r"(?:explain|analyze|analyse|check|review|read)\s+"
            r"(?:the\s+)?(?:file\s+)?([\\w./+-]+\\.[a-z0-9]+)",
            normalized
        )

        if match:
            filename = match.group(1)
            file_data, error = self.coding.read_file(filename)

            if error:
                return error

            prompt = self.coding.build_file_prompt(
                message,
                file_data
            )

            response = self.brain.get_response(
                prompt,
                memories=None
            )

            self.remember_ai_exchange(
                message,
                response
            )

            return response

        if (
            "active project" in normalized
            or "this project" in normalized
            or "my project" in normalized
        ) and any(
            word in normalized
            for word in (
                "explain",
                "analyze",
                "analyse",
                "review",
                "understand",
                "structure",
            )
        ):
            prompt, error = self.coding.build_project_prompt(
                message
            )

            if error:
                return error

            response = self.brain.get_response(
                prompt,
                memories=None
            )

            self.remember_ai_exchange(
                message,
                response
            )

            return response

        return None

    def is_coding_request(self, message):
        normalized = self.normalize_command(message)

        coding_terms = (
            "project files",
            "source files",
            "active project",
            "this project",
            "my project",
            "function ",
            "class ",
            "method ",
            "symbol ",
        )

        code_extensions = (
            ".py", ".js", ".ts", ".java", ".cpp",
            ".c", ".html", ".css", ".php"
        )

        return (
            any(term in normalized for term in coding_terms)
            or any(ext in normalized for ext in code_extensions)
        )

    # --------------------------------------------------
    # PROJECT / CODING WORKFLOW
    # --------------------------------------------------

    def handle_project_command(self, message):
        normalized = self.normalize_command(
            message
        )

        project_manager = self.commands.projects

        if normalized in {
            "scan for projects",
            "scan projects",
            "find my projects",
            "discover projects",
            "refresh projects",
        }:
            found = project_manager.discover_projects()

            return (
                f"🔎 Project scan finished. "
                f"I found or refreshed {len(found)} project folder(s).\n\n"
                + project_manager.list_projects()
            )

        if normalized in {
            "show my projects",
            "show projects",
            "list my projects",
            "list projects",
            "what projects do i have",
        }:
            return project_manager.list_projects()

        if normalized in {
            "show recent projects",
            "show my recent projects",
            "recent projects",
            "what are my recent projects",
        }:
            return project_manager.recent_projects()

        if normalized in {
            "what project am i working on",
            "what is my current project",
            "what's my current project",
            "whats my current project",
            "show current project",
            "show active project",
        }:
            return project_manager.active_project_info()

        # "open this project in VS Code"
        match = re.match(
            r"^open\s+(.+?)\s+in\s+(?:vs code|vscode|code)$",
            normalized
        )

        if match:
            name = match.group(1).strip()

            if name in {
                "this project",
                "the project",
                "current project",
                "this",
                "current",
            }:
                name = "this"

            return project_manager.open_in_vscode(
                name
            )

        # "open the project folder" / "open this project folder"
        if normalized in {
            "open the project folder",
            "open project folder",
            "open this project folder",
            "open current project folder",
            "show project folder",
            "show this project folder",
        }:
            return project_manager.open_project_folder(
                "this"
            )

        match = re.match(
            r"^(?:open|show)\s+(.+?)\s+project\s+folder$",
            normalized
        )

        if match:
            return project_manager.open_project_folder(
                match.group(1)
            )

        # "start coding mode for this project"
        match = re.match(
            r"^(?:start|open|launch)\s+coding\s+mode"
            r"(?:\s+for\s+(.+))?$",
            normalized
        )

        if match:
            name = (
                match.group(1)
                or "this"
            ).strip()

            if name in {
                "this project",
                "the project",
                "current project",
                "this",
                "current",
            }:
                name = "this"

            return project_manager.start_coding_mode(
                name
            )

        # "open my AkashAI project"
        match = re.match(
            r"^(?:open|launch|start)\s+"
            r"(?:my\s+)?(.+?)\s+project$",
            normalized
        )

        if match:
            name = match.group(1).strip()

            if name in {
                "this",
                "current",
                "the",
            }:
                name = "this"

            return project_manager.open_project(
                name
            )

        # "open this project"
        if normalized in {
            "open this project",
            "open current project",
            "open the project",
        }:
            return project_manager.open_project(
                "this"
            )

        return None

    def is_project_request(self, message):
        normalized = self.normalize_command(
            message
        )

        project_phrases = (
            " project",
            "projects",
            "coding mode",
            "project folder",
        )

        return any(
            phrase in normalized
            for phrase in project_phrases
        )

    # --------------------------------------------------
    # MAIN RESPONSE ROUTER
    # --------------------------------------------------

    def get_response(self, message):
        normalized = self.normalize_command(
            message
        )

        # ----------------------------------------------
        # PENDING REMINDER FOLLOW-UP
        # ----------------------------------------------
        # A reply such as "at 8 tonight" is not a reminder command by itself,
        # so it may otherwise be classified as normal conversation. If Jeroo
        # is already waiting for reminder details, finish that reminder before
        # any other routing takes place.
        if self.pending_reminder is not None:
            # A brand-new reminder command must replace any unfinished
            # reminder from an earlier conversation. Otherwise a phrase
            # like "remind me in 1 min" can be mistaken for the answer to
            # an old "what time?" question.
            fresh_reminder = (
                normalized.startswith("remind me")
                or normalized.startswith("set a reminder")
                or normalized.startswith("set reminder")
                or normalized.startswith("create a reminder")
            )

            if fresh_reminder:
                self.pending_reminder = None
            else:
                reminder_response = self._finish_pending_reminder(
                    message
                )

                if reminder_response is not None:
                    print(
                        "Jeroo intent: reminder_followup"
                    )
                    return reminder_response

        # ----------------------------------------------
        # RECENT CONVERSATION HISTORY
        # ----------------------------------------------

        history_response = self.handle_history_command(
            message
        )

        if history_response is not None:
            print(
                "Jeroo intent: conversation_history"
            )
            return history_response

        # ----------------------------------------------
        # WEB RESEARCH
        # ----------------------------------------------

        if self.is_web_research_request(
            message
        ):
            web_response = self.handle_web_research(
                message
            )

            if web_response is not None:
                print(
                    "Jeroo intent: web_research"
                )
                return web_response

        # ----------------------------------------------
        # LOCAL FILE ASSISTANT
        # ----------------------------------------------

        if self.is_file_request(
            message
        ):
            file_response = self.handle_file_command(
                message
            )

            if file_response is not None:
                print(
                    "Jeroo intent: file_assistant"
                )
                return file_response

        # ----------------------------------------------
        # CODING ASSISTANT
        # ----------------------------------------------

        if self.is_coding_request(
            message
        ):
            coding_response = self.handle_coding_command(
                message
            )

            if coding_response is not None:
                print(
                    "Jeroo intent: coding_assistant"
                )
                return coding_response

        # ----------------------------------------------
        # PROJECT / CODING WORKFLOW
        # ----------------------------------------------

        if self.is_project_request(
            message
        ):
            project_response = self.handle_project_command(
                message
            )

            if project_response is not None:
                print(
                    "Jeroo intent: project_workflow"
                )
                return project_response

        # ----------------------------------------------
        # SCREEN ACTION CONFIRMATION / PLANNING
        # ----------------------------------------------

        pending_screen_response = self.handle_pending_screen_action(
            message
        )

        if pending_screen_response is not None:
            print(
                "Jeroo intent: screen_action_confirmation"
            )
            return pending_screen_response

        if self.is_screen_action_request(
            message
        ):
            print(
                "Jeroo intent: screen_action_plan"
            )
            return self.plan_screen_action(
                message
            )

        # ----------------------------------------------
        # CONTEXTUAL FOLLOW-UP COMMANDS
        # ----------------------------------------------

        contextual_response = self.handle_context_followup(
            message
        )

        if contextual_response is not None:
            print(
                "Jeroo intent: contextual_action"
            )
            return contextual_response

        screen_context_response = self.handle_screen_context_followup(
            message
        )

        if screen_context_response is not None:
            print(
                "Jeroo intent: screen_context_followup"
            )
            return screen_context_response

        conversation_response = self.handle_conversation_followup(
            message
        )

        if conversation_response is not None:
            print(
                "Jeroo intent: conversation_followup"
            )
            return conversation_response

        smart_response = self.smart_route_request(
            message
        )

        if smart_response is not None:
            print(
                "Jeroo intent: smart_router"
            )
            return smart_response

        intent = self.intent_manager.classify(
            message=message,
            normalized=normalized,
            routine_exists=self.automation.routine_exists
        )

        print(
            f"Jeroo intent: {intent}"
        )

        # ----------------------------------------------
        # CUSTOM ROUTINES
        # ----------------------------------------------

        if intent == "routine":
            response = self.handle_routine_command(
                message
            )

            if response is not None:
                return response

        # ----------------------------------------------
        # NOTES / REMINDERS
        # ----------------------------------------------

        if intent == "automation":
            response = self.handle_automation_command(
                message
            )

            if response is not None:
                return response

        # ----------------------------------------------
        # MULTI-ACTION LOCAL COMMANDS
        # ----------------------------------------------

        if intent == "multi_action":
            response = self.run_multi_action(
                message
            )

            if response is not None:
                return response

        # ----------------------------------------------
        # ACTIVE WINDOW COMMANDS
        # ----------------------------------------------

        if intent == "active_window":
            response = self.handle_active_window_command(
                message
            )

            if response is not None:
                return response

        # ----------------------------------------------
        # MEMORY
        # ----------------------------------------------

        if intent == "memory":
            response = self.handle_memory_command(
                message
            )

            if response is not None:
                return response

        # ----------------------------------------------
        # SCREEN VISION
        # ----------------------------------------------

        if intent == "screen":
            return self.analyze_screen(
                message
            )

        # ----------------------------------------------
        # LOCAL PC COMMAND
        # ----------------------------------------------

        if intent == "local_command":
            response = self.commands.execute(
                normalized
            )

            if response is not None:
                self.remember_local_action(
                    normalized
                )
                return response

        # ----------------------------------------------
        # SAFETY FALLBACK
        # ----------------------------------------------
        # If an intent looked local but the local handler did not
        # understand it, try the normal command engine once before AI.
        # This preserves older commands added in earlier Jeroo versions.

        if intent != "ai":
            command_response = self.commands.execute(
                normalized
            )

            if command_response is not None:
                self.remember_local_action(
                    normalized
                )
                return command_response

        # ----------------------------------------------
        # AUTOMATIC LONG-TERM MEMORY DETECTION
        # ----------------------------------------------

        detected_memory = self.detect_memory(
            message
        )

        if detected_memory:
            self.memory.add(
                detected_memory
            )

        # ----------------------------------------------
        # AI CHAT + RELEVANT LONG-TERM MEMORY
        # ----------------------------------------------

        relevant_memories = self.memory.context_for(
            message,
            limit=8
        )

        response = self.brain.get_response(
            message,
            memories=relevant_memories
        )

        self.remember_ai_exchange(
            message,
            response
        )

        return response

