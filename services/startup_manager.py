import os
import sys
from pathlib import Path

try:
    import winreg
except ImportError:
    winreg = None


class StartupManager:

    RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
    VALUE_NAME = "JerroAI"

    def __init__(self):
        self.project_dir = Path(
            os.path.dirname(
                os.path.dirname(
                    os.path.abspath(__file__)
                )
            )
        )

        self.app_path = self.project_dir / "app.py"

    def _pythonw_path(self):
        executable = Path(sys.executable)

        if executable.name.lower() == "python.exe":
            candidate = executable.with_name("pythonw.exe")

            if candidate.exists():
                return candidate

        candidate = (
            self.project_dir
            / ".venv"
            / "Scripts"
            / "pythonw.exe"
        )

        if candidate.exists():
            return candidate

        return executable

    def startup_command(self):
        return (
            f'"{self._pythonw_path()}" '
            f'"{self.app_path}" --orb'
        )

    def enable(self):
        if winreg is None:
            return False, "Windows startup registration is unavailable."

        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                self.RUN_KEY,
                0,
                winreg.KEY_SET_VALUE
            )

            winreg.SetValueEx(
                key,
                self.VALUE_NAME,
                0,
                winreg.REG_SZ,
                self.startup_command()
            )

            winreg.CloseKey(key)

            return True, (
                "Jerro will start with Windows "
                "in floating orb mode."
            )

        except Exception as error:
            return False, f"Startup registration error: {error}"

    def disable(self):
        if winreg is None:
            return False, "Windows startup registration is unavailable."

        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                self.RUN_KEY,
                0,
                winreg.KEY_SET_VALUE
            )

            try:
                winreg.DeleteValue(
                    key,
                    self.VALUE_NAME
                )
            except FileNotFoundError:
                pass

            winreg.CloseKey(key)

            return True, "Jerro Windows startup disabled."

        except Exception as error:
            return False, f"Startup disable error: {error}"
