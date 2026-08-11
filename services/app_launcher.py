import os
import subprocess

from services.app_scanner import AppScanner


class AppLauncher:

    def __init__(self):

        # Existing built-in applications
        self.apps = {
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "calc": "calc.exe",
            "paint": "mspaint.exe",

            "chrome": "chrome.exe",
            "google chrome": "chrome.exe",

            "edge": "msedge.exe",
            "microsoft edge": "msedge.exe",

            "file explorer": "explorer.exe",
            "explorer": "explorer.exe",

            "command prompt": "cmd.exe",
            "cmd": "cmd.exe",

            "powershell": "powershell.exe",

            # Visual Studio Code
            "vs code": "code",
            "visual studio code": "code",
            "vscode": "code",
        }

        # Automatic Windows application scanner
        self.scanner = AppScanner()

        # Scan installed Start Menu applications
        self.scanned_apps = self.scanner.scan()

    # --------------------------------------------------
    # REFRESH APPLICATION LIST
    # --------------------------------------------------

    def refresh_apps(self):

        self.scanned_apps = self.scanner.scan()

        return self.scanned_apps

    # --------------------------------------------------
    # FIND APPLICATION
    # --------------------------------------------------

    def find_app(self, app_name):

        app_name = app_name.lower().strip()

        # Exact built-in application
        if app_name in self.apps:

            return {
                "type": "command",
                "value": self.apps[app_name]
            }

        # Exact scanned application
        if app_name in self.scanned_apps:

            return {
                "type": "shortcut",
                "value": self.scanned_apps[app_name]
            }

        # Partial match
        for name, shortcut in self.scanned_apps.items():

            if app_name in name or name in app_name:

                return {
                    "type": "shortcut",
                    "value": shortcut,
                    "name": name
                }

        return None

    # --------------------------------------------------
    # OPEN APPLICATION
    # --------------------------------------------------

    def open_app(self, app_name):

        app_name = app_name.lower().strip()

        result = self.find_app(app_name)

        # Nothing found
        if result is None:

            # Refresh scanner once
            self.refresh_apps()

            result = self.find_app(app_name)

        # Still not found
        if result is None:

            return (
                f"I couldn't find an application "
                f"called {app_name} on your PC."
            )

        try:

            # ------------------------------------------
            # Normal executable
            # ------------------------------------------

            if result["type"] == "command":

                subprocess.Popen(
                    result["value"],
                    shell=True
                )

                return f"Opening {app_name}."

            # ------------------------------------------
            # Windows Start Menu shortcut
            # ------------------------------------------

            if result["type"] == "shortcut":

                shortcut = result["value"]

                os.startfile(shortcut)

                actual_name = result.get(
                    "name",
                    app_name
                )

                return f"Opening {actual_name}."

        except Exception as e:

            return (
                f"I found {app_name}, "
                f"but I couldn't open it. "
                f"Error: {e}"
            )

        return (
            f"I couldn't open {app_name}."
        )

    # --------------------------------------------------
    # CHECK IF APPLICATION EXISTS
    # --------------------------------------------------

    def is_supported(self, app_name):

        return (
            self.find_app(app_name) is not None
        )

    # --------------------------------------------------
    # LIST APPLICATIONS
    # --------------------------------------------------

    def get_installed_apps(self):

        self.refresh_apps()

        return sorted(
            self.scanned_apps.keys()
        )