import os
import re
from pathlib import Path


class CodingAssistant:

    CODE_EXTENSIONS = {
        ".py", ".js", ".ts", ".jsx", ".tsx",
        ".java", ".cpp", ".cc", ".c", ".h", ".hpp",
        ".html", ".css", ".php", ".json", ".xml",
        ".md", ".txt"
    }

    IGNORE_DIRS = {
        ".git", ".venv", "venv", "node_modules",
        "__pycache__", "dist", "build", ".idea", ".vscode"
    }

    def __init__(self, project_manager):
        self.projects = project_manager

    def _project(self):
        return self.projects.get_active_project()

    def _root(self):
        project = self._project()

        if not project:
            return None

        path = project.get("path")

        if not path or not os.path.isdir(path):
            return None

        return Path(path)

    def list_files(self, limit=80):
        root = self._root()

        if not root:
            return None, "There isn't an active project yet."

        files = []

        for current, dirs, names in os.walk(root):
            dirs[:] = [
                d for d in dirs
                if d.lower() not in self.IGNORE_DIRS
            ]

            for name in names:
                path = Path(current) / name

                if path.suffix.lower() in self.CODE_EXTENSIONS:
                    try:
                        files.append(
                            str(path.relative_to(root))
                        )
                    except Exception:
                        pass

                    if len(files) >= limit:
                        return files, None

        return files, None

    def find_file(self, query):
        root = self._root()

        if not root:
            return None

        query = str(query or "").strip().lower()

        if not query:
            return None

        exact = []
        partial = []

        for current, dirs, names in os.walk(root):
            dirs[:] = [
                d for d in dirs
                if d.lower() not in self.IGNORE_DIRS
            ]

            for name in names:
                path = Path(current) / name
                relative = str(path.relative_to(root))
                low_name = name.lower()
                low_relative = relative.lower()

                if low_name == query or low_relative == query:
                    exact.append(path)
                elif query in low_name or query in low_relative:
                    partial.append(path)

        matches = exact or partial

        if len(matches) == 1:
            return matches[0]

        return matches if matches else None

    def read_file(self, query, max_chars=18000):
        result = self.find_file(query)

        if result is None:
            return None, f"I couldn't find '{query}' in the active project."

        if isinstance(result, list):
            root = self._root()
            names = [
                str(path.relative_to(root))
                for path in result[:12]
            ]

            return None, (
                "I found multiple matching files:\n"
                + "\n".join(f"• {name}" for name in names)
            )

        try:
            text = result.read_text(
                encoding="utf-8",
                errors="replace"
            )
        except Exception as error:
            return None, f"I couldn't read that file: {error}"

        if len(text) > max_chars:
            text = text[:max_chars] + "\n\n[File truncated for analysis]"

        return {
            "path": result,
            "relative": str(result.relative_to(self._root())),
            "text": text
        }, None

    def search_symbol(self, term, limit=30):
        root = self._root()

        if not root:
            return [], "There isn't an active project yet."

        term = str(term or "").strip()

        if not term:
            return [], "Tell me what function, class, or text to find."

        matches = []

        for current, dirs, names in os.walk(root):
            dirs[:] = [
                d for d in dirs
                if d.lower() not in self.IGNORE_DIRS
            ]

            for name in names:
                path = Path(current) / name

                if path.suffix.lower() not in self.CODE_EXTENSIONS:
                    continue

                try:
                    lines = path.read_text(
                        encoding="utf-8",
                        errors="replace"
                    ).splitlines()
                except Exception:
                    continue

                for number, line in enumerate(lines, 1):
                    if term.lower() in line.lower():
                        matches.append({
                            "file": str(path.relative_to(root)),
                            "line": number,
                            "text": line.strip()
                        })

                        if len(matches) >= limit:
                            return matches, None

        return matches, None

    def build_project_prompt(self, question):
        project = self._project()

        if not project:
            return None, "There isn't an active project yet."

        files, error = self.list_files(limit=60)

        if error:
            return None, error

        prompt = (
            "You are helping with the user's currently active coding project.\n"
            f"Project: {project.get('display_name', project.get('key'))}\n"
            f"Project path: {project.get('path')}\n\n"
            "Known source files:\n"
            + "\n".join(f"- {name}" for name in files)
            + "\n\nUser request:\n"
            + question
            + "\n\nDo not claim you inspected file contents unless they were "
              "included in the prompt. Give a practical answer."
        )

        return prompt, None

    def build_file_prompt(self, question, file_data):
        return (
            "You are Jeroo's coding assistant. Analyze the following file "
            "from the user's active project.\n\n"
            f"File: {file_data['relative']}\n\n"
            "FILE CONTENT:\n"
            "----------------\n"
            f"{file_data['text']}\n"
            "----------------\n\n"
            f"User request: {question}\n\n"
            "Be precise. Refer to the actual code above. If suggesting a "
            "change, explain it first. Do not claim the file was modified."
        )
