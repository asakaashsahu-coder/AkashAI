import json
import os
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path


class ProjectManager:

    PROJECT_MARKERS = {
        ".git",
        "package.json",
        "pyproject.toml",
        "requirements.txt",
        "pom.xml",
        "build.gradle",
        "build.gradle.kts",
        "composer.json",
        "Cargo.toml",
        "index.html",
    }

    def __init__(self):
        self.base_dir = Path(
            os.path.dirname(
                os.path.dirname(
                    os.path.abspath(__file__)
                )
            )
        )

        self.data_dir = self.base_dir / "data"
        self.data_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        self.projects_file = (
            self.data_dir / "projects.json"
        )

        self._ensure_registry()

        # Always make the current Jeroo project known.
        self.register_project(
            "akashai",
            str(self.base_dir),
            aliases=[
                "akash ai",
                "jeroo",
                "jeroo ai",
                "jerro",
                "jerro ai",
            ],
            touch_recent=False
        )

        self.folders = {
            "desktop": Path.home() / "Desktop",
            "downloads": Path.home() / "Downloads",
            "documents": Path.home() / "Documents",
            "pictures": Path.home() / "Pictures",
            "music": Path.home() / "Music",
            "videos": Path.home() / "Videos",
        }

    # ==================================================
    # REGISTRY HELPERS
    # ==================================================

    def _default_data(self):
        return {
            "active_project": "akashai",
            "projects": {},
            "recent": []
        }

    def _ensure_registry(self):
        if self.projects_file.exists():
            return

        self._save(
            self._default_data()
        )

    def _load(self):
        try:
            with open(
                self.projects_file,
                "r",
                encoding="utf-8"
            ) as file:
                data = json.load(file)

            if not isinstance(data, dict):
                raise ValueError(
                    "Invalid project registry."
                )

        except Exception:
            data = self._default_data()

        data.setdefault(
            "active_project",
            None
        )
        data.setdefault(
            "projects",
            {}
        )
        data.setdefault(
            "recent",
            []
        )

        return data

    def _save(self, data):
        with open(
            self.projects_file,
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
    # NORMALIZATION
    # ==================================================

    def normalize_name(self, name):
        name = str(
            name or ""
        ).strip().lower()

        name = re.sub(
            r"\b(project|folder|repo|repository)\b",
            " ",
            name
        )

        name = re.sub(
            r"[^a-z0-9+#._ -]",
            " ",
            name
        )

        return " ".join(
            name.split()
        )

    def display_name(self, key):
        data = self._load()
        project = data["projects"].get(
            key,
            {}
        )

        return project.get(
            "display_name",
            key
        )

    # ==================================================
    # REGISTER / ACTIVE / RECENT
    # ==================================================

    def register_project(
        self,
        name,
        path,
        aliases=None,
        touch_recent=True
    ):
        path_obj = Path(
            os.path.expandvars(
                os.path.expanduser(
                    str(path)
                )
            )
        )

        try:
            path_obj = path_obj.resolve()
        except Exception:
            pass

        if not path_obj.is_dir():
            return False

        key = self.normalize_name(
            name
        )

        if not key:
            key = self.normalize_name(
                path_obj.name
            )

        aliases = aliases or []

        normalized_aliases = []

        for alias in aliases:
            alias = self.normalize_name(
                alias
            )

            if (
                alias
                and alias not in normalized_aliases
            ):
                normalized_aliases.append(
                    alias
                )

        data = self._load()

        existing = data["projects"].get(
            key,
            {}
        )

        existing_aliases = existing.get(
            "aliases",
            []
        )

        for alias in existing_aliases:
            if alias not in normalized_aliases:
                normalized_aliases.append(
                    alias
                )

        data["projects"][key] = {
            "display_name": (
                existing.get("display_name")
                or path_obj.name
                or name
            ),
            "path": str(path_obj),
            "aliases": normalized_aliases,
            "last_opened": existing.get(
                "last_opened"
            ),
        }

        if touch_recent:
            self._touch_recent_in_data(
                data,
                key
            )

        self._save(
            data
        )

        return True

    def _touch_recent_in_data(
        self,
        data,
        key
    ):
        recent = [
            item
            for item in data.get(
                "recent",
                []
            )
            if item != key
        ]

        recent.insert(
            0,
            key
        )

        data["recent"] = recent[:15]
        data["active_project"] = key

        project = data["projects"].get(
            key
        )

        if project is not None:
            project["last_opened"] = (
                datetime.now().isoformat(
                    timespec="seconds"
                )
            )

    def set_active_project(
        self,
        key
    ):
        data = self._load()

        if key not in data["projects"]:
            return False

        self._touch_recent_in_data(
            data,
            key
        )

        self._save(
            data
        )

        return True

    def get_active_project(self):
        data = self._load()

        key = data.get(
            "active_project"
        )

        if (
            key
            and key in data["projects"]
        ):
            project = dict(
                data["projects"][key]
            )

            project["key"] = key

            return project

        return None

    # ==================================================
    # DISCOVERY
    # ==================================================

    def discovery_roots(self):
        roots = []

        home = Path.home()

        candidates = [
            home / "Desktop",
            home / "Documents",
            home / "Downloads",
            home / "Projects",
            home / "source",
            home / "repos",
            self.base_dir.parent,
        ]

        onedrive = os.environ.get(
            "OneDrive"
        )

        if onedrive:
            candidates.extend([
                Path(onedrive),
                Path(onedrive) / "Desktop",
                Path(onedrive) / "Documents",
                Path(onedrive) / "Pictures",
            ])

        seen = set()

        for root in candidates:
            try:
                root = root.resolve()
            except Exception:
                pass

            if (
                root.is_dir()
                and str(root).lower() not in seen
            ):
                seen.add(
                    str(root).lower()
                )
                roots.append(
                    root
                )

        return roots

    def looks_like_project(
        self,
        folder
    ):
        try:
            names = {
                item.name
                for item in folder.iterdir()
            }
        except Exception:
            return False

        if names & self.PROJECT_MARKERS:
            return True

        code_extensions = {
            ".py",
            ".js",
            ".ts",
            ".java",
            ".cpp",
            ".c",
            ".html",
            ".css",
            ".php",
        }

        code_count = 0

        try:
            for item in folder.iterdir():
                if (
                    item.is_file()
                    and item.suffix.lower()
                    in code_extensions
                ):
                    code_count += 1

                    if code_count >= 2:
                        return True
        except Exception:
            pass

        return False

    def discover_projects(
        self,
        max_depth=2,
        max_projects=50
    ):
        found = []

        ignored = {
            ".git",
            ".venv",
            "venv",
            "node_modules",
            "__pycache__",
            "appdata",
            "windows",
        }

        for root in self.discovery_roots():
            root_depth = len(
                root.parts
            )

            for current, dirs, files in os.walk(
                root
            ):
                current_path = Path(
                    current
                )

                depth = (
                    len(current_path.parts)
                    - root_depth
                )

                dirs[:] = [
                    name
                    for name in dirs
                    if name.lower() not in ignored
                    and not name.startswith(".")
                ]

                if depth > max_depth:
                    dirs[:] = []
                    continue

                if self.looks_like_project(
                    current_path
                ):
                    name = current_path.name

                    if self.register_project(
                        name,
                        str(current_path),
                        touch_recent=False
                    ):
                        found.append(
                            str(current_path)
                        )

                    dirs[:] = []

                    if len(found) >= max_projects:
                        return found

        return found

    # ==================================================
    # RESOLUTION
    # ==================================================

    def resolve_project(
        self,
        project_name
    ):
        name = self.normalize_name(
            project_name
        )

        if name in {
            "this",
            "current",
            "active",
            "this one",
            "current one",
        }:
            return self.get_active_project()

        data = self._load()

        if name in data["projects"]:
            project = dict(
                data["projects"][name]
            )
            project["key"] = name
            return project

        for key, project in data[
            "projects"
        ].items():
            aliases = project.get(
                "aliases",
                []
            )

            candidates = [
                key,
                self.normalize_name(
                    project.get(
                        "display_name",
                        ""
                    )
                ),
                *aliases
            ]

            if name in candidates:
                result = dict(
                    project
                )
                result["key"] = key
                return result

        # Fuzzy contains match for natural project names.
        matches = []

        for key, project in data[
            "projects"
        ].items():
            display = self.normalize_name(
                project.get(
                    "display_name",
                    ""
                )
            )

            if (
                name
                and (
                    name in key
                    or name in display
                    or key in name
                    or display in name
                )
            ):
                matches.append(
                    (key, project)
                )

        if len(matches) == 1:
            key, project = matches[0]

            result = dict(
                project
            )
            result["key"] = key
            return result

        return None

    # ==================================================
    # OPEN HELPERS
    # ==================================================

    def _find_vscode(self):
        code_cmd = shutil.which(
            "code"
        ) or shutil.which(
            "code.cmd"
        )

        if code_cmd:
            return [
                code_cmd
            ]

        local = os.environ.get(
            "LOCALAPPDATA",
            ""
        )

        program_files = os.environ.get(
            "PROGRAMFILES",
            r"C:\Program Files"
        )

        candidates = [
            Path(local)
            / "Programs"
            / "Microsoft VS Code"
            / "Code.exe",

            Path(program_files)
            / "Microsoft VS Code"
            / "Code.exe",
        ]

        for candidate in candidates:
            if candidate.exists():
                return [
                    str(candidate)
                ]

        return None

    def open_in_vscode(
        self,
        project_name
    ):
        project = self.resolve_project(
            project_name
        )

        if not project:
            return (
                f"I don't know the project "
                f"'{project_name}' yet. "
                "Try 'scan for projects'."
            )

        path = project.get(
            "path"
        )

        if not path or not os.path.isdir(
            path
        ):
            return (
                "I found the project entry, but its "
                "folder no longer exists."
            )

        vscode = self._find_vscode()

        if not vscode:
            return (
                "I found the project, but I couldn't "
                "find VS Code on this PC."
            )

        try:
            subprocess.Popen(
                vscode + [path],
                shell=False
            )

            self.set_active_project(
                project["key"]
            )

            return (
                f"💻 Opening {project['display_name']} "
                "in VS Code."
            )

        except Exception as error:
            return (
                "I couldn't open the project in VS Code.\n"
                f"Error: {error}"
            )

    def open_project_folder(
        self,
        project_name
    ):
        project = self.resolve_project(
            project_name
        )

        if not project:
            return (
                f"I don't know the project "
                f"'{project_name}' yet. "
                "Try 'scan for projects'."
            )

        path = project.get(
            "path"
        )

        if not path or not os.path.isdir(
            path
        ):
            return (
                "I found the project entry, but its "
                "folder no longer exists."
            )

        try:
            os.startfile(
                path
            )

            self.set_active_project(
                project["key"]
            )

            return (
                f"📁 Opening {project['display_name']} "
                "project folder."
            )

        except Exception as error:
            return (
                "I couldn't open the project folder.\n"
                f"Error: {error}"
            )

    def open_project(
        self,
        project_name
    ):
        project = self.resolve_project(
            project_name
        )

        if not project:
            # One discovery pass can find newly-created projects.
            self.discover_projects()

            project = self.resolve_project(
                project_name
            )

        if not project:
            return (
                f"I don't know the project "
                f"'{project_name}' yet. "
                "Try 'scan for projects'."
            )

        path = project.get(
            "path"
        )

        if not path or not os.path.isdir(
            path
        ):
            return (
                "I found the project entry, but its "
                "folder no longer exists."
            )

        folder_ok = False
        code_ok = False

        try:
            os.startfile(
                path
            )
            folder_ok = True
        except Exception:
            pass

        vscode = self._find_vscode()

        if vscode:
            try:
                subprocess.Popen(
                    vscode + [path],
                    shell=False
                )
                code_ok = True
            except Exception:
                pass

        self.set_active_project(
            project["key"]
        )

        if code_ok and folder_ok:
            return (
                f"🚀 Opening {project['display_name']} "
                "in VS Code and File Explorer."
            )

        if code_ok:
            return (
                f"💻 Opening {project['display_name']} "
                "in VS Code."
            )

        if folder_ok:
            return (
                f"📁 Opening {project['display_name']} "
                "project folder. I couldn't find VS Code."
            )

        return (
            f"I couldn't open {project['display_name']}."
        )

    def start_coding_mode(
        self,
        project_name
    ):
        project = self.resolve_project(
            project_name
        )

        if not project:
            return (
                f"I don't know the project "
                f"'{project_name}' yet. "
                "Try 'scan for projects'."
            )

        path = project.get(
            "path"
        )

        if not path or not os.path.isdir(
            path
        ):
            return (
                "The saved project folder no longer exists."
            )

        results = []

        vscode = self._find_vscode()

        if vscode:
            try:
                subprocess.Popen(
                    vscode + [path],
                    shell=False
                )
                results.append(
                    "VS Code"
                )
            except Exception:
                pass

        try:
            os.startfile(
                path
            )
            results.append(
                "project folder"
            )
        except Exception:
            pass

        self.set_active_project(
            project["key"]
        )

        if not results:
            return (
                f"I couldn't start coding mode for "
                f"{project['display_name']}."
            )

        return (
            f"🧑‍💻 Coding mode started for "
            f"{project['display_name']}: "
            + " + ".join(results)
            + "."
        )

    # ==================================================
    # LISTS / INFO
    # ==================================================

    def list_projects(self):
        data = self._load()

        if not data["projects"]:
            return (
                "I don't have any projects saved yet."
            )

        lines = []

        for key, project in sorted(
            data["projects"].items(),
            key=lambda item: (
                item[1].get(
                    "display_name",
                    item[0]
                ).lower()
            )
        ):
            marker = (
                "  ← active"
                if key == data.get(
                    "active_project"
                )
                else ""
            )

            lines.append(
                f"• {project.get('display_name', key)}"
                f"{marker}"
            )

        return (
            "📚 Projects I know:\n\n"
            + "\n".join(lines[:30])
        )

    def recent_projects(
        self,
        limit=8
    ):
        data = self._load()

        lines = []

        for key in data.get(
            "recent",
            []
        )[:limit]:
            project = data[
                "projects"
            ].get(
                key
            )

            if project:
                lines.append(
                    f"• {project.get('display_name', key)}"
                )

        if not lines:
            return (
                "I don't have any recent projects yet."
            )

        return (
            "🕘 Recent projects:\n\n"
            + "\n".join(lines)
        )

    def active_project_info(self):
        project = self.get_active_project()

        if not project:
            return (
                "There isn't an active project yet."
            )

        return (
            f"📌 Current project: "
            f"{project.get('display_name', project['key'])}\n"
            f"{project.get('path', '')}"
        )

    # ==================================================
    # COMMON WINDOWS FOLDERS
    # ==================================================

    def open_folder(
        self,
        folder_name
    ):
        folder_name = (
            str(folder_name)
            .lower()
            .strip()
        )

        if folder_name not in self.folders:
            return (
                f"I don't know the folder "
                f"{folder_name} yet."
            )

        path = self.folders[
            folder_name
        ]

        if not path.is_dir():
            return (
                f"I couldn't find:\n{path}"
            )

        try:
            os.startfile(
                str(path)
            )

            return (
                f"Opening {folder_name}."
            )

        except Exception as error:
            return (
                f"I couldn't open {folder_name}.\n"
                f"Error: {error}"
            )
