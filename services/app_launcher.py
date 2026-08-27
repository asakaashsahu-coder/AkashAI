import ctypes
import difflib
import os
import re
import shutil
import subprocess
from pathlib import Path


class AppLauncher:

    def __init__(self):
        self.apps = {}
        self.scan_apps()

        self.aliases = {
            "browser": "chrome",
            "my browser": "chrome",
            "google chrome": "chrome",
            "chrome browser": "chrome",

            "code": "visual studio code",
            "vs code": "visual studio code",
            "vscode": "visual studio code",
            "code editor": "visual studio code",
            "my code editor": "visual studio code",

            "files": "file explorer",
            "file manager": "file explorer",
            "explorer": "file explorer",

            "terminal": "powershell",
            "shell": "powershell",

            "calc": "calculator",
        }

        # Executable/process names are useful for close/switch operations.
        self.process_aliases = {
            "chrome": "chrome.exe",
            "google chrome": "chrome.exe",
            "visual studio code": "Code.exe",
            "vs code": "Code.exe",
            "vscode": "Code.exe",
            "spotify": "Spotify.exe",
            "discord": "Discord.exe",
            "edge": "msedge.exe",
            "microsoft edge": "msedge.exe",
            "notepad": "notepad.exe",
            "calculator": "CalculatorApp.exe",
            "powershell": "powershell.exe",
        }

    # ==================================================
    # NORMALIZATION
    # ==================================================

    def normalize(self, name):
        name = name.lower().strip()

        name = re.sub(
            r"\.(exe|lnk|url)$",
            "",
            name
        )

        name = re.sub(
            r"[^a-z0-9+#.\s-]",
            " ",
            name
        )

        return " ".join(name.split())

    def resolve_alias(self, name):
        normalized = self.normalize(name)
        return self.aliases.get(
            normalized,
            normalized
        )

    # ==================================================
    # WINDOWS APP DISCOVERY
    # ==================================================

    def scan_apps(self):
        self.apps = {}

        start_menu_paths = [
            Path(os.environ.get("APPDATA", "")) /
            "Microsoft/Windows/Start Menu/Programs",

            Path(os.environ.get("PROGRAMDATA", "")) /
            "Microsoft/Windows/Start Menu/Programs",
        ]

        for root in start_menu_paths:
            if not root.exists():
                continue

            try:
                for item in root.rglob("*"):
                    if item.suffix.lower() not in {
                        ".lnk",
                        ".url",
                        ".exe",
                    }:
                        continue

                    key = self.normalize(
                        item.stem
                    )

                    if key and key not in self.apps:
                        self.apps[key] = str(item)

            except Exception as error:
                print(
                    "App scan error:",
                    error
                )

    # ==================================================
    # KNOWN WINDOWS INSTALL LOCATIONS
    # ==================================================

    def known_app_paths(self):
        local = os.environ.get(
            "LOCALAPPDATA",
            ""
        )

        program_files = os.environ.get(
            "PROGRAMFILES",
            r"C:\Program Files"
        )

        program_files_x86 = os.environ.get(
            "PROGRAMFILES(X86)",
            r"C:\Program Files (x86)"
        )

        appdata = os.environ.get(
            "APPDATA",
            ""
        )

        return {
            "chrome": [
                os.path.join(
                    program_files,
                    "Google",
                    "Chrome",
                    "Application",
                    "chrome.exe"
                ),
                os.path.join(
                    program_files_x86,
                    "Google",
                    "Chrome",
                    "Application",
                    "chrome.exe"
                ),
                os.path.join(
                    local,
                    "Google",
                    "Chrome",
                    "Application",
                    "chrome.exe"
                ),
            ],

            "visual studio code": [
                os.path.join(
                    local,
                    "Programs",
                    "Microsoft VS Code",
                    "Code.exe"
                ),
                os.path.join(
                    program_files,
                    "Microsoft VS Code",
                    "Code.exe"
                ),
            ],

            "spotify": [
                os.path.join(
                    appdata,
                    "Spotify",
                    "Spotify.exe"
                ),
                os.path.join(
                    local,
                    "Microsoft",
                    "WindowsApps",
                    "Spotify.exe"
                ),
            ],

            "discord": [
                os.path.join(
                    local,
                    "Discord",
                    "Update.exe"
                ),
            ],

            "edge": [
                os.path.join(
                    program_files_x86,
                    "Microsoft",
                    "Edge",
                    "Application",
                    "msedge.exe"
                ),
                os.path.join(
                    program_files,
                    "Microsoft",
                    "Edge",
                    "Application",
                    "msedge.exe"
                ),
            ],
        }

    def find_known_app(self, name):
        known = self.known_app_paths()

        aliases = {
            "google chrome": "chrome",
            "chrome browser": "chrome",
            "microsoft edge": "edge",
            "vs code": "visual studio code",
            "vscode": "visual studio code",
        }

        key = aliases.get(
            name,
            name
        )

        for path in known.get(
            key,
            []
        ):
            if path and os.path.exists(path):
                return path

        return None

    # ==================================================
    # BUILT-IN WINDOWS APPS
    # ==================================================

    def open_builtin(self, name):
        builtins = {
            "notepad": ["notepad.exe"],
            "calculator": ["calc.exe"],
            "file explorer": ["explorer.exe"],
            "powershell": ["powershell.exe"],
            "command prompt": ["cmd.exe"],
            "cmd": ["cmd.exe"],
            "task manager": ["taskmgr.exe"],
            "settings": [
                "cmd",
                "/c",
                "start",
                "",
                "ms-settings:"
            ],
        }

        command = builtins.get(name)

        if not command:
            return False

        try:
            if (
                isinstance(command, list)
                and len(command) == 1
            ):
                subprocess.Popen(
                    command,
                    shell=False
                )
            else:
                subprocess.Popen(
                    command,
                    shell=False
                )

            return True

        except Exception as error:
            print(
                f"Built-in launch error ({name}):",
                error
            )

            return False

    # ==================================================
    # FIND START MENU APP
    # ==================================================

    def find_scanned_app(self, name):
        if name in self.apps:
            return self.apps[name]

        # Prefer names that contain the requested app name.
        containing = [
            key
            for key in self.apps
            if name in key
        ]

        if containing:
            best = min(
                containing,
                key=len
            )
            return self.apps[best]

        matches = difflib.get_close_matches(
            name,
            list(self.apps.keys()),
            n=1,
            cutoff=0.72
        )

        if matches:
            return self.apps[
                matches[0]
            ]

        return None

    # ==================================================
    # OPEN APP
    # ==================================================

    def open_app(self, app_name):
        name = self.resolve_alias(
            app_name
        )

        # 1. Native Windows apps.
        if self.open_builtin(name):
            return (
                f"🚀 Opening {app_name}."
            )

        # 2. Real known installation path.
        known_path = self.find_known_app(
            name
        )

        if known_path:
            try:
                # Discord's Update.exe needs the process argument.
                if (
                    name == "discord"
                    and known_path.lower().endswith(
                        "update.exe"
                    )
                ):
                    subprocess.Popen(
                        [
                            known_path,
                            "--processStart",
                            "Discord.exe"
                        ],
                        shell=False
                    )
                else:
                    subprocess.Popen(
                        [known_path],
                        shell=False
                    )

                return (
                    f"🚀 Opening {app_name}."
                )

            except Exception as error:
                print(
                    "Known app launch error:",
                    error
                )

        # 3. Start Menu shortcut discovered by scanner.
        scanned = self.find_scanned_app(
            name
        )

        if scanned:
            try:
                os.startfile(
                    scanned
                )

                return (
                    f"🚀 Opening {app_name}."
                )

            except Exception as error:
                print(
                    "Start Menu launch error:",
                    error
                )

        # 4. Only use PATH if Windows can actually resolve it.
        executable_candidates = {
            "chrome": "chrome.exe",
            "visual studio code": "Code.exe",
            "edge": "msedge.exe",
            "spotify": "Spotify.exe",
        }

        executable = executable_candidates.get(
            name
        )

        if executable:
            resolved = shutil.which(
                executable
            )

            if resolved:
                try:
                    subprocess.Popen(
                        [resolved],
                        shell=False
                    )

                    return (
                        f"🚀 Opening {app_name}."
                    )

                except Exception as error:
                    print(
                        "PATH launch error:",
                        error
                    )

        return (
            f"❌ I couldn't find {app_name}. "
            "Try 'list apps' to see what Jeroo detected."
        )

    # Backward-compatible names used by earlier Jeroo versions.
    def launch(self, app_name):
        return self.open_app(
            app_name
        )

    def open(self, app_name):
        return self.open_app(
            app_name
        )

    # ==================================================
    # PROCESS NAME
    # ==================================================

    def get_process_name(self, app_name):
        name = self.resolve_alias(
            app_name
        )

        if name in self.process_aliases:
            return self.process_aliases[
                name
            ]

        # Fallback for ordinary executable names.
        cleaned = re.sub(
            r"[^a-zA-Z0-9_.-]",
            "",
            app_name
        )

        if not cleaned:
            return None

        if not cleaned.lower().endswith(
            ".exe"
        ):
            cleaned += ".exe"

        return cleaned

    # ==================================================
    # CLOSE PROCESS (ACTIVE-WINDOW COMPATIBILITY)
    # ==================================================

    def close_process(
        self,
        process_name,
        display_name=None
    ):
        process = (
            process_name
            or ""
        ).strip()

        if not process:
            return "❌ I couldn't identify the application process."

        if not process.lower().endswith(
            ".exe"
        ):
            process += ".exe"

        protected = {
            "explorer.exe",
            "dwm.exe",
            "winlogon.exe",
            "csrss.exe",
            "services.exe",
            "lsass.exe",
            "svchost.exe",
            "system.exe",
            "python.exe",
            "pythonw.exe",
        }

        if process.lower() in protected:
            return (
                "🛡️ I won't close that protected "
                "Windows/Jeroo process."
            )

        result = subprocess.run(
            [
                "taskkill",
                "/IM",
                process,
                "/F"
            ],
            capture_output=True,
            text=True,
            shell=False
        )

        name = (
            display_name
            or process_name
        )

        if result.returncode == 0:
            return f"🛑 Closed {name}."

        return (
            f"❌ I couldn't close {name}. "
            "It may no longer be running."
        )

    # ==================================================
    # CLOSE APP
    # ==================================================

    def close_app(self, app_name):
        process = self.get_process_name(
            app_name
        )

        if not process:
            return (
                f"❌ I couldn't identify {app_name}."
            )

        protected = {
            "explorer.exe",
            "dwm.exe",
            "winlogon.exe",
            "csrss.exe",
            "services.exe",
            "lsass.exe",
            "system",
            "python.exe",
            "pythonw.exe",
        }

        if process.lower() in protected:
            return (
                f"🛡️ I won't close the protected "
                f"process {process}."
            )

        result = subprocess.run(
            [
                "taskkill",
                "/IM",
                process,
                "/F"
            ],
            capture_output=True,
            text=True,
            shell=False
        )

        if result.returncode == 0:
            return (
                f"🛑 Closed {app_name}."
            )

        return (
            f"❌ I couldn't close {app_name}. "
            "It may not be running."
        )

    # ==================================================
    # SWITCH / FOCUS APP
    # ==================================================

    def switch_to_app(self, app_name):
        process_name = self.get_process_name(
            app_name
        )

        if not process_name:
            return (
                f"❌ I couldn't identify {app_name}."
            )

        try:
            user32 = ctypes.windll.user32

            EnumWindows = user32.EnumWindows
            IsWindowVisible = user32.IsWindowVisible
            GetWindowThreadProcessId = (
                user32.GetWindowThreadProcessId
            )
            SetForegroundWindow = (
                user32.SetForegroundWindow
            )
            ShowWindow = user32.ShowWindow

            kernel32 = ctypes.windll.kernel32

            PROCESS_QUERY_LIMITED_INFORMATION = (
                0x1000
            )

            found = {
                "hwnd": None
            }

            @ctypes.WINFUNCTYPE(
                ctypes.c_bool,
                ctypes.c_void_p,
                ctypes.c_void_p
            )
            def callback(hwnd, lparam):
                if not IsWindowVisible(hwnd):
                    return True

                pid = ctypes.c_ulong()

                GetWindowThreadProcessId(
                    hwnd,
                    ctypes.byref(pid)
                )

                handle = kernel32.OpenProcess(
                    PROCESS_QUERY_LIMITED_INFORMATION,
                    False,
                    pid.value
                )

                if not handle:
                    return True

                try:
                    buffer = ctypes.create_unicode_buffer(
                        1024
                    )

                    size = ctypes.c_ulong(
                        len(buffer)
                    )

                    ok = kernel32.QueryFullProcessImageNameW(
                        handle,
                        0,
                        buffer,
                        ctypes.byref(size)
                    )

                    if ok:
                        current = os.path.basename(
                            buffer.value
                        )

                        if (
                            current.lower()
                            == process_name.lower()
                        ):
                            found["hwnd"] = hwnd
                            return False

                finally:
                    kernel32.CloseHandle(
                        handle
                    )

                return True

            EnumWindows(
                callback,
                0
            )

            hwnd = found["hwnd"]

            if not hwnd:
                return (
                    f"❌ I couldn't find an open "
                    f"{app_name} window."
                )

            ShowWindow(
                hwnd,
                9
            )

            SetForegroundWindow(
                hwnd
            )

            return (
                f"🪟 Switched to {app_name}."
            )

        except Exception as error:
            print(
                "Switch app error:",
                error
            )

            return (
                f"❌ I couldn't switch to {app_name}."
            )

    # ==================================================
    # LIST DETECTED APPS
    # ==================================================

    def list_apps(self):
        names = sorted(
            self.apps.keys()
        )

        if not names:
            return (
                "I couldn't find any Start Menu apps."
            )

        # Keep the response useful instead of dumping hundreds of entries.
        visible = names[:50]

        text = "\n".join(
            f"• {name}"
            for name in visible
        )

        if len(names) > 50:
            text += (
                f"\n• ...and {len(names) - 50} more"
            )

        return (
            "📱 Apps Jeroo detected:\n\n"
            + text
        )
