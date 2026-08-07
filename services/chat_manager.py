import json
import os


class ChatManager:

    def __init__(self):

        self.chat_folder = "data/chats"

        os.makedirs(self.chat_folder, exist_ok=True)

        self.current_chat = "chat1.json"

        self.current_path = os.path.join(
            self.chat_folder,
            self.current_chat
        )

        if not os.path.exists(self.current_path):
            with open(self.current_path, "w") as file:
                json.dump([], file, indent=4)

    def load_chat(self):

        with open(self.current_path, "r") as file:
            return json.load(file)

    def save_message(self, role, message):

        history = self.load_chat()

        history.append({
            "role": role,
            "message": message
        })

        with open(self.current_path, "w") as file:
            json.dump(history, file, indent=4)

    def clear_chat(self):

        with open(self.current_path, "w") as file:
            json.dump([], file, indent=4)

    def create_new_chat(self):

        files = [
            file for file in os.listdir(self.chat_folder)
            if file.endswith(".json")
        ]

        chat_number = len(files) + 1

        self.current_chat = f"chat{chat_number}.json"

        self.current_path = os.path.join(
            self.chat_folder,
            self.current_chat
        )

        with open(self.current_path, "w") as file:
            json.dump([], file, indent=4)

    def get_chat_list(self):

        return sorted(
            [
                file
                for file in os.listdir(self.chat_folder)
                if file.endswith(".json")
            ]
        )

    def switch_chat(self, filename):

        self.current_chat = filename

        self.current_path = os.path.join(
            self.chat_folder,
            filename
        )