import json
import os
import re
import threading
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()


class Brain:

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY is missing from the .env file."
            )

        self.client = genai.Client(
            api_key=api_key
        )

        self.model = os.getenv(
            "GEMINI_MODEL",
            "gemini-3.5-flash"
        )

        # Keep vision separate so a text-model change does not break
        # screen analysis. You can override this in .env with:
        # GEMINI_VISION_MODEL=gemini-3.6-flash
        self.vision_model = os.getenv(
            "GEMINI_VISION_MODEL",
            "gemini-3.6-flash"
        )

        project_root = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )

        self.history_file = os.path.join(
            project_root,
            "data",
            "chat_history.json"
        )

        os.makedirs(
            os.path.dirname(self.history_file),
            exist_ok=True
        )

        self.max_saved_messages = 40
        self.lock = threading.Lock()

        self.system_prompt = """
You are Jeroo, Akash's personal desktop AI assistant.

IDENTITY
- Your name is Jeroo.
- You were created by Akash Kumar Sahu.
- If someone asks who you are, say naturally that you are Jeroo, Akash's personal AI assistant.
- Do not call yourself Gemini, Google AI, or a Google language model unless the user specifically asks what model powers you.

CONVERSATION STYLE
Talk like a real person, not like a help-desk bot.

- Be warm, natural, relaxed, and emotionally aware.
- Match the user's energy without copying them excessively.
- Use contractions naturally: "I'm", "you're", "that's", "don't", "can't".
- Prefer conversational sentences over formal report-style writing.
- Keep ordinary replies short unless the user asks for detail.
- Do not turn every response into headings, bullet lists, or numbered steps.
- Do not repeatedly say things like "Certainly", "Of course", "I'd be happy to help", or "How may I assist you?"
- Do not repeat the user's question before answering it.
- Do not keep introducing yourself unless it is relevant.
- Do not end every message with an offer such as "Let me know if you need anything else."
- Use small natural reactions when appropriate, such as "Nice", "Hmm", "Oh", "Got it", "Wait", "Yeah", or "That makes sense". Do not force them into every reply.
- Light humor is fine when the moment fits. Never force jokes.
- If the user is excited, you may sound more energetic.
- If the user is frustrated, be calmer and more focused.
- If something is surprising, you may react naturally before explaining it.
- If the user is casual, you can be casual too.
- If the situation is serious, drop playful language and be direct.

EMOTIONAL INTELLIGENCE
Respond to the emotional tone of the conversation, but do not pretend to have human feelings, a body, consciousness, or experiences you do not have.

You may sound:
- calm
- cheerful
- excited
- curious
- amused
- concerned
- reassuring
- serious

Express emotion through wording, pacing, and punctuation rather than announcing labels such as "I am excited" or "Emotion: happy".

NATURAL DIALOGUE
Treat conversation as continuous.

- Use recent conversation context naturally.
- Understand short follow-ups such as "why?", "really?", "then what?", "do it", "nah", and "what about this?" when context makes them clear.
- Refer back to earlier parts of the conversation when useful.
- Do not restate information the user already knows unless needed.
- If the user is brainstorming, think with them rather than giving a finished lecture immediately.
- When a yes/no answer is enough, answer yes/no first and then add only the useful detail.
- When the user is just chatting, chat back naturally instead of turning everything into a task.

SPEAKING-FRIENDLY RESPONSES
Many of your replies will be spoken aloud.

- Write responses that sound good when spoken.
- Prefer short-to-medium sentences.
- Use commas and periods for natural pauses.
- Avoid excessive parentheses, semicolons, symbols, Markdown, and nested lists in conversational replies.
- Avoid reading out long URLs unless necessary.
- When explaining code or technical material, the displayed response can still contain code and structure, but surrounding explanation should remain natural.

HELPFULNESS
You can help with programming, AI, web development, learning, productivity, general questions, and everyday tasks.

Use saved user memories only when relevant. Do not repeatedly mention memory. If saved memory conflicts with what the user says now, trust the newest user message.

Never pretend that you performed a computer action unless the local Jeroo system actually performed it.
Never claim to see the user's screen unless screen analysis was actually provided.

Most importantly: sound like Jeroo having a genuine conversation with the user, not an AI generating a customer-support response.
""".strip()

        self.history = self.load_history()

    # --------------------------------------------------
    # HISTORY STORAGE
    # --------------------------------------------------

    def load_history(self):
        try:
            with open(
                self.history_file,
                "r",
                encoding="utf-8"
            ) as file:
                data = json.load(file)

            if not isinstance(data, list):
                return []

            clean_history = []

            for item in data:
                if not isinstance(item, dict):
                    continue

                role = item.get("role")
                text = item.get("text")

                # Backward compatibility if a previous version stored
                # Gemini-style "parts" instead of plain text.
                if not text:
                    parts = item.get("parts", [])

                    if parts and isinstance(parts, list):
                        first_part = parts[0]

                        if isinstance(first_part, dict):
                            text = first_part.get("text")

                if role not in ("user", "model"):
                    continue

                if not isinstance(text, str) or not text.strip():
                    continue

                clean_history.append({
                    "role": role,
                    "text": text.strip()
                })

            return clean_history[-self.max_saved_messages:]

        except (
            FileNotFoundError,
            json.JSONDecodeError,
            OSError
        ):
            return []

    def save_history(self):
        history_to_save = self.history[-self.max_saved_messages:]

        with open(
            self.history_file,
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(
                history_to_save,
                file,
                indent=4,
                ensure_ascii=False
            )

    def clear_history(self):
        with self.lock:
            self.history = []
            self.save_history()

        return True

    def get_history(self):
        return list(self.history)

    # --------------------------------------------------
    # BUILD GEMINI CONTENTS
    # --------------------------------------------------

    def build_contents(self, message, memories=None):
        contents = [
            {
                "role": "user",
                "parts": [
                    {
                        "text": self.system_prompt
                    }
                ]
            }
        ]

        # Only send the recent part of the conversation to keep requests
        # fast and avoid unnecessary token usage.
        recent_history = self.history[-self.max_saved_messages:]

        for item in recent_history:
            contents.append({
                "role": item["role"],
                "parts": [
                    {
                        "text": item["text"]
                    }
                ]
            })

        current_message = message

        if memories:
            memory_text = "\n".join(
                f"- {memory}"
                for memory in memories
            )

            current_message += (
                "\n\nSaved user memory for context "
                "(use only if relevant):\n"
                f"{memory_text}"
            )

        contents.append({
            "role": "user",
            "parts": [
                {
                    "text": current_message
                }
            ]
        })

        return contents

    # --------------------------------------------------
    # FIND RETRY DELAY FROM GEMINI ERROR
    # --------------------------------------------------

    def get_retry_delay(self, error):
        error_text = str(error)

        match = re.search(
            r"retry in ([0-9.]+)s",
            error_text,
            re.IGNORECASE
        )

        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass

        return 5

    # --------------------------------------------------
    # CHECK IF ERROR IS A QUOTA / RATE LIMIT ERROR
    # --------------------------------------------------

    def is_quota_error(self, error):
        error_text = str(error).lower()

        return (
            "429" in error_text
            or "resource_exhausted" in error_text
            or "quota exceeded" in error_text
            or "rate limit" in error_text
        )

    # --------------------------------------------------
    # GET RESPONSE
    # --------------------------------------------------

    def get_response(self, message, memories=None):
        message = message.strip()

        if not message:
            return "What would you like to ask?"

        # Keep requests sequential so two fast messages cannot corrupt
        # the saved conversation order.
        with self.lock:
            contents = self.build_contents(
                message,
                memories=memories
            )

            max_retries = 2

            for attempt in range(max_retries + 1):
                try:
                    print(
                        f"Contacting Gemini... "
                        f"(attempt {attempt + 1}/{max_retries + 1})"
                    )

                    response = self.client.models.generate_content(
                        model=self.model,
                        contents=contents
                    )

                    answer = response.text

                    if not answer:
                        return (
                            "Sorry, I received an empty response. "
                            "Please try again."
                        )

                    answer = answer.strip()

                    # Save only the clean conversation. The injected memory
                    # context is intentionally not written into chat history.
                    self.history.append({
                        "role": "user",
                        "text": message
                    })

                    self.history.append({
                        "role": "model",
                        "text": answer
                    })

                    self.history = self.history[
                        -self.max_saved_messages:
                    ]

                    self.save_history()

                    return answer

                except Exception as e:
                    print(
                        "Gemini Error:",
                        e
                    )

                    if self.is_quota_error(e):
                        delay = self.get_retry_delay(e)

                        if attempt < max_retries:
                            print(
                                "Gemini rate limit detected."
                            )

                            print(
                                f"Waiting {delay:.1f} seconds "
                                "before retry..."
                            )

                            time.sleep(delay)
                            continue

                        return (
                            "I have temporarily reached the "
                            "free AI request limit. "
                            "Please wait a little and try again."
                        )

                    return (
                        "Sorry, I couldn't contact the AI "
                        "service right now. Please try again."
                    )

            return (
                "Sorry, I couldn't get a response from the "
                "AI service."
            )

    # --------------------------------------------------
    # SCREEN / VISION RESPONSE
    # --------------------------------------------------

    def get_screen_response(
        self,
        message,
        image_bytes,
        memories=None
    ):
        message = message.strip()

        if not message:
            message = "What is on my screen?"

        if not image_bytes:
            return "I couldn't capture your screen to analyze it."

        print(
            f"Screen captured: {len(image_bytes):,} bytes"
        )

        with self.lock:
            context_text = message

            if memories:
                memory_text = "\n".join(
                    f"- {memory}"
                    for memory in memories
                )

                context_text += (
                    "\n\nSaved user memory for context "
                    "(use only if relevant):\n"
                    f"{memory_text}"
                )

            screen_instruction = (
                "\n\nYou are analyzing a screenshot of the user's "
                "current Windows desktop. The image attached to this "
                "message IS the user's screen. Describe what is actually "
                "visible in the image and answer the user's request from "
                "that visual information. Do not say that you cannot see "
                "the screen unless the attached image is genuinely blank "
                "or unreadable. If text is too small, say which part is "
                "unclear instead of guessing. If the user asks what to "
                "click, describe the visible control and where it is. "
                "Do not claim you clicked anything."
            )

            prompt_part = types.Part.from_text(
                text=context_text + screen_instruction
            )

            image_part = types.Part.from_bytes(
                data=image_bytes,
                mime_type="image/png"
            )

            # Keep the request purely multimodal and avoid mixing old
            # dictionary-style content objects with typed Content objects.
            contents = [
                types.Content(
                    role="user",
                    parts=[
                        prompt_part,
                        image_part
                    ]
                )
            ]

            # First try the dedicated vision model. If that model is not
            # available for this account, fall back to Jeroo's main model.
            model_candidates = []

            for candidate in [
                self.vision_model,
                "gemini-3.6-flash",
                self.model,
            ]:
                if candidate and candidate not in model_candidates:
                    model_candidates.append(candidate)

            last_error = None

            for model_name in model_candidates:
                try:
                    print(
                        f"Analyzing screen with {model_name}..."
                    )

                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=contents
                    )

                    answer = getattr(
                        response,
                        "text",
                        None
                    )

                    if not answer:
                        last_error = (
                            f"{model_name} returned an empty response."
                        )
                        continue

                    answer = answer.strip()

                    # Guard against a text-only-style refusal even though
                    # an image was attached. Try another model if available.
                    refusal_phrases = [
                        "can't see your screen",
                        "cannot see your screen",
                        "can't view your screen",
                        "cannot view your screen",
                        "i don't have access to your screen",
                        "i do not have access to your screen",
                    ]

                    if any(
                        phrase in answer.lower()
                        for phrase in refusal_phrases
                    ):
                        print(
                            f"{model_name} ignored the attached image; "
                            "trying another vision model."
                        )
                        last_error = answer
                        continue

                    self.history.append({
                        "role": "user",
                        "text": "[Screen analysis] " + message
                    })

                    self.history.append({
                        "role": "model",
                        "text": answer
                    })

                    self.history = self.history[
                        -self.max_saved_messages:
                    ]

                    self.save_history()

                    return answer

                except Exception as error:
                    last_error = error

                    print(
                        f"Screen analysis error with {model_name}:",
                        error
                    )

                    # If this is quota/rate limiting, another model can
                    # sometimes still be available, so keep trying.
                    continue

            print(
                "All screen-analysis models failed:",
                last_error
            )

            return (
                "I captured your screen successfully, but the vision "
                "model couldn't analyze the image right now. "
                "Please try again in a moment."
            )

