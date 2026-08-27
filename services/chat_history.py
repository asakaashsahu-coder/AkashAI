import json
import os
import threading
import uuid
from datetime import datetime


class ChatHistoryManager:

    def __init__(self):
        base_dir = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )

        self.data_dir = os.path.join(
            base_dir,
            "data"
        )

        os.makedirs(
            self.data_dir,
            exist_ok=True
        )

        self.history_file = os.path.join(
            self.data_dir,
            "chat_history.json"
        )

        self.lock = threading.Lock()

        if not os.path.exists(self.history_file):
            self._save({
                "active_chat_id": None,
                "chats": []
            })

    # ==================================================
    # FILE HELPERS
    # ==================================================

    def _load(self):
        try:
            with open(
                self.history_file,
                "r",
                encoding="utf-8"
            ) as file:
                data = json.load(file)

            if not isinstance(data, dict):
                raise ValueError("Invalid history format")

            data.setdefault(
                "active_chat_id",
                None
            )

            data.setdefault(
                "chats",
                []
            )

            return data

        except Exception:
            return {
                "active_chat_id": None,
                "chats": []
            }

    def _save(self, data):
        with open(
            self.history_file,
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(
                data,
                file,
                indent=2,
                ensure_ascii=False
            )

    # ==================================================
    # CHAT CREATION
    # ==================================================

    def create_chat(self):
        now = datetime.now().isoformat(
            timespec="seconds"
        )

        chat = {
            "id": uuid.uuid4().hex,
            "title": "New conversation",
            "created_at": now,
            "updated_at": now,
            "messages": []
        }

        with self.lock:
            data = self._load()

            data["chats"].insert(
                0,
                chat
            )

            data["active_chat_id"] = chat["id"]

            self._save(data)

        return chat

    # ==================================================
    # ACTIVE CHAT
    # ==================================================

    def get_active_chat(self):
        with self.lock:
            data = self._load()

            active_id = data.get(
                "active_chat_id"
            )

            if active_id:
                for chat in data["chats"]:
                    if chat["id"] == active_id:
                        return chat

        return self.create_chat()

    def set_active_chat(self, chat_id):
        with self.lock:
            data = self._load()

            exists = any(
                chat["id"] == chat_id
                for chat in data["chats"]
            )

            if not exists:
                return False

            data["active_chat_id"] = chat_id
            self._save(data)

        return True

    # ==================================================
    # MESSAGES
    # ==================================================

    def add_message(
        self,
        chat_id,
        sender,
        message
    ):
        with self.lock:
            data = self._load()

            target = None

            for chat in data["chats"]:
                if chat["id"] == chat_id:
                    target = chat
                    break

            if target is None:
                return False

            target["messages"].append({
                "sender": str(sender),
                "message": str(message),
                "time": datetime.now().isoformat(
                    timespec="seconds"
                )
            })

            target["updated_at"] = datetime.now().isoformat(
                timespec="seconds"
            )

            if (
                target["title"] == "New conversation"
                and sender.lower() == "you"
            ):
                target["title"] = self._make_title(
                    str(message)
                )

            data["chats"] = sorted(
                data["chats"],
                key=lambda chat: chat.get(
                    "updated_at",
                    ""
                ),
                reverse=True
            )

            self._save(data)

        return True

    def replace_messages(
        self,
        chat_id,
        messages
    ):
        with self.lock:
            data = self._load()

            for chat in data["chats"]:
                if chat["id"] == chat_id:
                    chat["messages"] = messages
                    chat["updated_at"] = (
                        datetime.now().isoformat(
                            timespec="seconds"
                        )
                    )
                    self._save(data)
                    return True

        return False

    # ==================================================
    # LIST / GET
    # ==================================================

    def list_chats(self, limit=30):
        with self.lock:
            data = self._load()

        chats = sorted(
            data["chats"],
            key=lambda chat: chat.get(
                "updated_at",
                ""
            ),
            reverse=True
        )

        return chats[:limit]

    def get_chat(self, chat_id):
        with self.lock:
            data = self._load()

            for chat in data["chats"]:
                if chat["id"] == chat_id:
                    return chat

        return None

    # ==================================================
    # DELETE
    # ==================================================

    def delete_chat(self, chat_id):
        with self.lock:
            data = self._load()

            old_count = len(
                data["chats"]
            )

            data["chats"] = [
                chat
                for chat in data["chats"]
                if chat["id"] != chat_id
            ]

            if len(data["chats"]) == old_count:
                return False

            if data.get(
                "active_chat_id"
            ) == chat_id:
                data["active_chat_id"] = None

            self._save(data)

        return True

    # ==================================================
    # TITLE
    # ==================================================

    def _make_title(self, text):
        clean = " ".join(
            text.strip().split()
        )

        if not clean:
            return "New conversation"

        words = clean.split()

        title = " ".join(
            words[:7]
        )

        if len(words) > 7:
            title += "..."

        return title[:60]
