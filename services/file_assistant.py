import os
import re
from datetime import datetime, timedelta
from pathlib import Path


class FileAssistant:
    """Safe local file discovery, reading and opening for Jeroo."""

    TEXT_EXTENSIONS = {
        ".txt", ".md", ".py", ".js", ".ts", ".jsx", ".tsx",
        ".java", ".cpp", ".cc", ".c", ".h", ".hpp",
        ".html", ".css", ".php", ".json", ".xml", ".csv",
        ".log", ".ini", ".yaml", ".yml"
    }

    IGNORE_DIRS = {
        ".git", ".venv", "venv", "node_modules",
        "__pycache__", "appdata", "$recycle.bin"
    }

    def __init__(self):
        self.home = Path.home()
        self.last_results = []

    def search_roots(self):
        roots = []

        candidates = [
            self.home / "Desktop",
            self.home / "Documents",
            self.home / "Downloads",
            self.home / "Pictures",
        ]

        onedrive = os.environ.get("OneDrive")

        if onedrive:
            candidates.extend([
                Path(onedrive) / "Desktop",
                Path(onedrive) / "Documents",
                Path(onedrive) / "Pictures",
                Path(onedrive),
            ])

        seen = set()

        for root in candidates:
            try:
                root = root.resolve()
            except Exception:
                pass

            key = str(root).lower()

            if root.is_dir() and key not in seen:
                seen.add(key)
                roots.append(root)

        return roots

    def find_files(self, query, limit=25, modified_after=None):
        query = str(query or "").strip().lower()
        results = []

        for root in self.search_roots():
            for current, dirs, names in os.walk(root):
                dirs[:] = [
                    d for d in dirs
                    if d.lower() not in self.IGNORE_DIRS
                    and not d.startswith(".")
                ]

                for name in names:
                    if query and query not in name.lower():
                        continue

                    path = Path(current) / name

                    try:
                        stat = path.stat()
                    except Exception:
                        continue

                    if (
                        modified_after is not None
                        and datetime.fromtimestamp(stat.st_mtime) < modified_after
                    ):
                        continue

                    results.append({
                        "path": path,
                        "name": name,
                        "modified": datetime.fromtimestamp(stat.st_mtime),
                    })

                    if len(results) >= limit:
                        self.last_results = results
                        return results

        results.sort(
            key=lambda item: item["modified"],
            reverse=True
        )

        self.last_results = results
        return results

    def recent_files(self, hours=24, limit=20):
        cutoff = datetime.now() - timedelta(hours=hours)
        return self.find_files(
            "",
            limit=limit,
            modified_after=cutoff
        )

    def format_results(self, results, title="Files"):
        if not results:
            return "I couldn't find any matching files."

        lines = []

        for index, item in enumerate(results, 1):
            lines.append(
                f"{index}. {item['name']} — {item['path']}"
            )

        return f"📁 {title}:\n\n" + "\n".join(lines)

    def resolve_last_result(self, number):
        try:
            index = int(number) - 1
        except Exception:
            return None

        if 0 <= index < len(self.last_results):
            return self.last_results[index]["path"]

        return None

    def open_path(self, path):
        path = Path(path)

        if not path.exists():
            return "That file no longer exists."

        try:
            os.startfile(str(path))
            return f"📂 Opening {path.name}."
        except Exception as error:
            return f"I couldn't open that file: {error}"

    def read_path(self, path, max_chars=18000):
        path = Path(path)

        if not path.exists():
            return None, "That file no longer exists."

        if path.suffix.lower() not in self.TEXT_EXTENSIONS:
            return None, (
                f"{path.name} isn't a plain-text file I can safely "
                "read directly yet, but I can open it for you."
            )

        try:
            text = path.read_text(
                encoding="utf-8",
                errors="replace"
            )
        except Exception as error:
            return None, f"I couldn't read that file: {error}"

        if len(text) > max_chars:
            text = text[:max_chars] + "\n\n[File truncated]"

        return text, None
