import webbrowser
from urllib.parse import quote_plus


class WebManager:

    def __init__(self):

        self.websites = {
            "google": "https://www.google.com",
            "youtube": "https://www.youtube.com",
            "github": "https://github.com",
            "gmail": "https://mail.google.com",
            "chatgpt": "https://chatgpt.com",
            "stackoverflow": "https://stackoverflow.com",
        }

    def open_website(self, name):

        name = name.lower().strip()

        if name not in self.websites:
            return f"I don't know the website {name} yet."

        url = self.websites[name]

        try:
            webbrowser.open_new_tab(url)

            return f"Opening {name}."

        except Exception as e:
            return f"I couldn't open {name}. Error: {e}"

    def google_search(self, query):

        query = query.strip()

        if not query:
            return "What would you like me to search for?"

        url = (
            "https://www.google.com/search?q="
            + quote_plus(query)
        )

        try:
            webbrowser.open_new_tab(url)

            return f"Searching Google for {query}."

        except Exception as e:
            return f"I couldn't perform the search. Error: {e}"

    def youtube_search(self, query):

        query = query.strip()

        if not query:
            return "What would you like me to search on YouTube?"

        url = (
            "https://www.youtube.com/results?search_query="
            + quote_plus(query)
        )

        try:
            webbrowser.open_new_tab(url)

            return f"Searching YouTube for {query}."

        except Exception as e:
            return f"I couldn't search YouTube. Error: {e}"