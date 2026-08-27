import json
import os
import shutil
from datetime import datetime


class SettingsManager:

    DEFAULTS = {
        "appearance": "Dark",
        "ui_scale": "100%",
        "voice_enabled": True,
        "wake_phrase_enabled": False,
        "default_browser": "Chrome"
    }

    def __init__(self):
        base_dir = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )

        self.base_dir = base_dir
        self.data_dir = os.path.join(base_dir, "data")
        os.makedirs(self.data_dir, exist_ok=True)

        self.settings_file = os.path.join(
            self.data_dir,
            "settings.json"
        )

        self.backup_dir = os.path.join(
            self.data_dir,
            "backups"
        )

        os.makedirs(
            self.backup_dir,
            exist_ok=True
        )

        if not os.path.exists(self.settings_file):
            self._save(dict(self.DEFAULTS))

    def _load(self):
        try:
            with open(
                self.settings_file,
                "r",
                encoding="utf-8"
            ) as file:
                data = json.load(file)

            if not isinstance(data, dict):
                data = {}

        except Exception:
            data = {}

        merged = dict(self.DEFAULTS)
        merged.update(data)
        return merged

    def _save(self, data):
        with open(
            self.settings_file,
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(
                data,
                file,
                indent=2,
                ensure_ascii=False
            )

    def get_all(self):
        return self._load()

    def get(self, key, default=None):
        return self._load().get(
            key,
            default
        )

    def set(self, key, value):
        data = self._load()
        data[key] = value
        self._save(data)
        return value

    def reset(self):
        self._save(
            dict(self.DEFAULTS)
        )
        return dict(self.DEFAULTS)

    def export_data(self):
        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        destination = os.path.join(
            self.backup_dir,
            f"jeroo_backup_{timestamp}"
        )

        os.makedirs(
            destination,
            exist_ok=True
        )

        copied = []

        for filename in [
            "settings.json",
            "chat_history.json",
            "memory.json",
            "notes.json",
            "reminders.json",
            "routines.json",
        ]:
            source = os.path.join(
                self.data_dir,
                filename
            )

            if os.path.exists(source):
                shutil.copy2(
                    source,
                    os.path.join(
                        destination,
                        filename
                    )
                )
                copied.append(filename)

        return destination, copied

    def clear_chat_history(self):
        path = os.path.join(
            self.data_dir,
            "chat_history.json"
        )

        with open(
            path,
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(
                {
                    "active_chat_id": None,
                    "chats": []
                },
                file,
                indent=2
            )

    def clear_memory_file(self):
        # Memory implementations can differ between Jeroo versions.
        # Only clear known local JSON memory files; do not touch code.
        candidates = [
            "memory.json",
            "memories.json"
        ]

        cleared = False

        for filename in candidates:
            path = os.path.join(
                self.data_dir,
                filename
            )

            if os.path.exists(path):
                with open(
                    path,
                    "w",
                    encoding="utf-8"
                ) as file:
                    json.dump(
                        [],
                        file,
                        indent=2
                    )
                cleared = True

        return cleared
