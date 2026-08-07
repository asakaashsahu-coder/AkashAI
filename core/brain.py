import os

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

        try:

            response = self.client.models.generate_content(
                model="gemini-3.5-flash",
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

            print("Gemini Error:", e)

            return (
                "⚠️ Sorry, I couldn't contact the AI service right now."
            )