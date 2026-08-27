import ctypes
import json
import os
import threading
import time
from datetime import datetime, timedelta


class AutomationManager:

    def __init__(self):
        base_dir = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )

        self.data_dir = os.path.join(base_dir, "data")
        os.makedirs(self.data_dir, exist_ok=True)

        self.notes_file = os.path.join(self.data_dir, "notes.json")
        self.reminders_file = os.path.join(self.data_dir, "reminders.json")

        self.lock = threading.Lock()
        self.running = True

        self._ensure_file(self.notes_file, [])
        self._ensure_file(self.reminders_file, [])

        self.worker = threading.Thread(
            target=self._reminder_loop,
            daemon=True
        )
        self.worker.start()

    def _ensure_file(self, path, default):
        if not os.path.exists(path):
            self._save(path, default)

    def _load(self, path, default):
        try:
            with open(path, "r", encoding="utf-8") as file:
                return json.load(file)
        except Exception:
            return default

    def _save(self, path, data):
        with open(path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2, ensure_ascii=False)

    # ==================================================
    # NOTES
    # ==================================================

    def add_note(self, text):
        text = text.strip()

        if not text:
            return "What should I write in the note?"

        with self.lock:
            notes = self._load(self.notes_file, [])
            notes.append({
                "text": text,
                "created_at": datetime.now().isoformat(timespec="seconds")
            })
            self._save(self.notes_file, notes)

        return f"📝 Note saved: {text}"

    def list_notes(self):
        with self.lock:
            notes = self._load(self.notes_file, [])

        if not notes:
            return "📝 You don't have any saved notes."

        return (
            "📝 Your recent notes:\n\n"
            + "\n".join(
                f"• {item.get('text', '')}"
                for item in notes[-10:]
            )
        )

    def clear_notes(self):
        with self.lock:
            self._save(self.notes_file, [])

        return "🧹 All notes cleared."

    # ==================================================
    # REMINDERS
    # ==================================================

    def add_reminder(self, task, minutes):
        task = task.strip()

        if not task:
            return "What should I remind you about?"

        if minutes <= 0:
            return "The reminder time needs to be greater than zero."

        due = datetime.now() + timedelta(minutes=minutes)

        with self.lock:
            reminders = self._load(self.reminders_file, [])
            reminders.append({
                "task": task,
                "due_at": due.isoformat(timespec="seconds"),
                "done": False
            })
            self._save(self.reminders_file, reminders)

        when = due.strftime("%I:%M %p").lstrip("0")
        return f"⏰ Reminder set for {when}: {task}"

    def list_reminders(self):
        with self.lock:
            reminders = self._load(self.reminders_file, [])

        active = [
            item for item in reminders
            if not item.get("done", False)
        ]

        if not active:
            return "⏰ You don't have any active reminders."

        lines = []

        for item in active[:10]:
            try:
                due = datetime.fromisoformat(item["due_at"])
                when = due.strftime("%d %b, %I:%M %p").lstrip("0")
            except Exception:
                when = item.get("due_at", "unknown time")

            lines.append(
                f"• {when} — {item.get('task', '')}"
            )

        return "⏰ Active reminders:\n\n" + "\n".join(lines)

    def clear_reminders(self):
        with self.lock:
            self._save(self.reminders_file, [])

        return "🧹 All reminders cleared."


    # ==================================================
    # ROUTINES
    # ==================================================

    def _routines_file(self):
        return os.path.join(
            self.data_dir,
            "routines.json"
        )

    def _load_routines(self):
        path = self._routines_file()

        if not os.path.exists(path):
            self._save(path, {})

        data = self._load(path, {})

        if not isinstance(data, dict):
            return {}

        return data

    def _save_routines(self, routines):
        self._save(
            self._routines_file(),
            routines
        )

    def save_routine(self, name, actions):
        name = " ".join(name.strip().lower().split())

        actions = [
            " ".join(action.strip().split())
            for action in actions
            if action.strip()
        ]

        if not name:
            return "What should I call the routine?"

        if not actions:
            return "A routine needs at least one action."

        if len(actions) > 10:
            return "A routine can contain up to 10 actions."

        with self.lock:
            routines = self._load_routines()

            replacing = name in routines

            routines[name] = {
                "name": name,
                "actions": actions,
                "updated_at": datetime.now().isoformat(
                    timespec="seconds"
                )
            }

            self._save_routines(routines)

        if replacing:
            return (
                f"⚙️ Updated routine '{name}' with "
                f"{len(actions)} action(s)."
            )

        return (
            f"⚙️ Created routine '{name}' with "
            f"{len(actions)} action(s)."
        )

    def get_routine(self, name):
        name = " ".join(name.strip().lower().split())

        with self.lock:
            routines = self._load_routines()

        routine = routines.get(name)

        if not routine:
            return None

        actions = routine.get("actions", [])

        if not isinstance(actions, list):
            return None

        return actions

    def routine_exists(self, name):
        return self.get_routine(name) is not None

    def list_routines(self):
        with self.lock:
            routines = self._load_routines()

        if not routines:
            return "⚙️ You don't have any custom routines yet."

        lines = []

        for name in sorted(routines):
            actions = routines[name].get(
                "actions",
                []
            )

            preview = "; ".join(actions[:3])

            if len(actions) > 3:
                preview += f"; +{len(actions) - 3} more"

            lines.append(
                f"• {name}: {preview}"
            )

        return (
            "⚙️ Your routines:\n\n"
            + "\n".join(lines)
        )

    def describe_routine(self, name):
        name = " ".join(name.strip().lower().split())

        actions = self.get_routine(name)

        if actions is None:
            return f"I couldn't find a routine called '{name}'."

        return (
            f"⚙️ Routine '{name}':\n\n"
            + "\n".join(
                f"{index}. {action}"
                for index, action in enumerate(
                    actions,
                    start=1
                )
            )
        )

    def delete_routine(self, name):
        name = " ".join(name.strip().lower().split())

        with self.lock:
            routines = self._load_routines()

            if name not in routines:
                return (
                    f"I couldn't find a routine "
                    f"called '{name}'."
                )

            routines.pop(name)

            self._save_routines(routines)

        return f"🗑️ Deleted routine '{name}'."

    # ==================================================
    # BACKGROUND REMINDER WORKER
    # ==================================================

    def _reminder_loop(self):
        while self.running:
            try:
                self._check_due_reminders()
            except Exception as error:
                print("Reminder worker error:", error)

            time.sleep(5)

    def _check_due_reminders(self):
        now = datetime.now()
        due_items = []

        with self.lock:
            reminders = self._load(self.reminders_file, [])
            changed = False

            for item in reminders:
                if item.get("done", False):
                    continue

                try:
                    due = datetime.fromisoformat(item["due_at"])
                except Exception:
                    continue

                if due <= now:
                    item["done"] = True
                    due_items.append(item.get("task", "Reminder"))
                    changed = True

            if changed:
                self._save(self.reminders_file, reminders)

        for task in due_items:
            self._show_reminder(task)

    def _show_reminder(self, task):
        try:
            ctypes.windll.user32.MessageBoxW(
                0,
                task,
                "Jeroo Reminder",
                0x00001040
            )
        except Exception as error:
            print(f"⏰ Reminder: {task}")
            print("Reminder popup error:", error)
