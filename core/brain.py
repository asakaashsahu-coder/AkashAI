
import os
import time
import re

from dotenv import load_dotenv
from google import genai

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

        self.model = "gemini-3.5-flash"

        self.history = [
            {
                "role": "user",
                "parts": [
                    {
                        "text": """
You are Jeroo.

You are a personal desktop AI assistant created by Akash Kumar Sahu.

Always introduce yourself as Jeroo.

Never say you are Gemini, Google AI, or a Google language model unless the user specifically asks which AI model powers you.

If someone asks "Who are you?", answer:

"I am Jeroo, your personal AI assistant created by Akash Kumar Sahu. I'm here to help with programming, AI, web development, productivity, and everyday tasks."

Be friendly, intelligent, professional and concise.

Help the user with:

- Programming
- AI
- Web development
- Learning
- Productivity
- General questions
- Everyday tasks

Do not pretend to perform actions that you cannot actually perform.
"""
                    }
                ]
            }
        ]

    # --------------------------------------------------
    # FIND RETRY DELAY FROM GEMINI ERROR
    # --------------------------------------------------

    def get_retry_delay(self, error):

        error_text = str(error)

        # Example:
        # "Please retry in 23.471187599s"
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

        # Safe default if Gemini doesn't provide
        # a retry time.
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

    def get_response(self, message):

        self.history.append(
            {
                "role": "user",
                "parts": [
                    {
                        "text": message
                    }
                ]
            }
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
                    contents=self.history
                )

                answer = response.text

                self.history.append(
                    {
                        "role": "model",
                        "parts": [
                            {
                                "text": answer
                            }
                        ]
                    }
                )

                return answer

            except Exception as e:

                print(
                    "Gemini Error:",
                    e
                )

                # ------------------------------------------
                # QUOTA / RATE LIMIT
                # ------------------------------------------

                if self.is_quota_error(e):

                    delay = self.get_retry_delay(e)

                    # If this is not the last retry,
                    # wait and try again.
                    if attempt < max_retries:

                        print(
                            f"Gemini rate limit detected."
                        )

                        print(
                            f"Waiting {delay:.1f} seconds "
                            f"before retry..."
                        )

                        time.sleep(delay)

                        continue

                    # --------------------------------------
                    # ALL RETRIES USED
                    # --------------------------------------

                    return (
                        "I have temporarily reached the "
                        "free AI request limit. "
                        "Please wait a little and try again."
                    )

                # ------------------------------------------
                # OTHER AI / NETWORK ERROR
                # ------------------------------------------

                return (
                    "Sorry, I couldn't contact the AI "
                    "service right now. Please try again."
                )

        return (
            "Sorry, I couldn't get a response from the "
            "AI service."
        )

