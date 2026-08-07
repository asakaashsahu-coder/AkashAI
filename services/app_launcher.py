import os
import subprocess


class AppLauncher:

    def __init__(self):

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

    def open_app(self, app_name):

        app_name = app_name.lower().strip()

        if app_name not in self.apps:

            return (
                f"I don't know how to open "
                f"{app_name} yet."
            )

        command = self.apps[app_name]

        try:

            subprocess.Popen(
                command,
                shell=True
            )

            return f"Opening {app_name}."

        except Exception as e:

            return (
                f"I couldn't open {app_name}. "
                f"Error: {e}"
            )

    def is_supported(self, app_name):

        return (
            app_name.lower().strip()
            in self.apps
        )