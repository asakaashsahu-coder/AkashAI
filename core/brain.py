import os
from dotenv import load_dotenv
from google import genai

load_dotenv()


class Brain:

    def __init__(self):

        self.client = genai.Client(
            api_key=os.getenv("GEMINI_API_KEY")
        )

        self.history = [
            {
                "role": "user",
                "parts": [{
                    "text": (
                        "You are AkashAI, a personal AI assistant created by Akash. "
                        "Never say you are Gemini or Google unless directly asked about your underlying model. "
                        "Introduce yourself as AkashAI. "
                        "Be friendly, professional, and concise."
                    )
                }]
            },
            {
                "role": "model",
                "parts": [{
                    "text": "Understood. I am AkashAI."
                }]
            }
        ]

    def get_response(self, message):

        self.history.append(
            {
                "role": "user",
                "parts": [{"text": message}]
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
                    "parts": [{"text": answer}]
                }
            )

            return answer

        except Exception as e:
            return f"Error: {e}"