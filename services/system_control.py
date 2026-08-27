import os
import subprocess
from datetime import datetime
from pathlib import Path


class SystemControl:

    # =========================================
    # VOLUME
    # =========================================

    def volume_up(self):

        try:

            for _ in range(5):

                subprocess.run(
                    [
                        "powershell",
                        "-NoProfile",
                        "-Command",
                        "(New-Object -ComObject WScript.Shell).SendKeys([char]175)"
                    ],
                    capture_output=True
                )

            return "Volume increased."

        except Exception as e:

            return (
                f"I couldn't increase the volume. "
                f"Error: {e}"
            )

    def volume_down(self):

        try:

            for _ in range(5):

                subprocess.run(
                    [
                        "powershell",
                        "-NoProfile",
                        "-Command",
                        "(New-Object -ComObject WScript.Shell).SendKeys([char]174)"
                    ],
                    capture_output=True
                )

            return "Volume decreased."

        except Exception as e:

            return (
                f"I couldn't decrease the volume. "
                f"Error: {e}"
            )

    def mute(self):

        try:

            subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    "(New-Object -ComObject WScript.Shell).SendKeys([char]173)"
                ],
                capture_output=True
            )

            return "Audio mute toggled."

        except Exception as e:

            return (
                f"I couldn't change the mute state. "
                f"Error: {e}"
            )

    # =========================================
    # BATTERY STATUS
    # =========================================

    def battery_status(self):

        try:

            command = (
                "$battery = Get-CimInstance Win32_Battery | Select-Object -First 1; "
                "if ($null -eq $battery) { Write-Output 'NO_BATTERY' } "
                "else { Write-Output ($battery.EstimatedChargeRemaining.ToString() + '|' + "
                "$battery.BatteryStatus.ToString()) }"
            )

            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    command,
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            output = result.stdout.strip()

            if not output or output == "NO_BATTERY":
                return "I couldn't detect a battery on this computer."

            percentage, status_code = output.split("|", 1)

            status_names = {
                "1": "discharging",
                "2": "connected to power",
                "3": "fully charged",
                "4": "low",
                "5": "critical",
                "6": "charging",
                "7": "charging",
                "8": "charging",
                "9": "charging",
                "10": "undefined",
                "11": "partially charged",
            }

            state = status_names.get(
                status_code.strip(),
                "status unknown"
            )

            return (
                f"Your battery is at {percentage}% "
                f"and is {state}."
            )

        except Exception as e:

            return (
                "I couldn't read the battery status. "
                f"Error: {e}"
            )

    # =========================================
    # SCREENSHOT
    # =========================================

    def take_screenshot(self):

        try:

            pictures = Path.home() / "Pictures"
            screenshot_folder = pictures / "Jeroo Screenshots"
            screenshot_folder.mkdir(
                parents=True,
                exist_ok=True
            )

            timestamp = datetime.now().strftime(
                "%Y-%m-%d_%H-%M-%S"
            )

            screenshot_path = (
                screenshot_folder
                / f"Jeroo_Screenshot_{timestamp}.png"
            )

            safe_path = str(screenshot_path).replace(
                "'",
                "''"
            )

            command = (
                "Add-Type -AssemblyName System.Windows.Forms; "
                "Add-Type -AssemblyName System.Drawing; "
                "$bounds = [System.Windows.Forms.SystemInformation]::VirtualScreen; "
                "$bitmap = New-Object System.Drawing.Bitmap($bounds.Width, $bounds.Height); "
                "$graphics = [System.Drawing.Graphics]::FromImage($bitmap); "
                "$graphics.CopyFromScreen($bounds.Left, $bounds.Top, 0, 0, $bitmap.Size); "
                f"$bitmap.Save('{safe_path}', [System.Drawing.Imaging.ImageFormat]::Png); "
                "$graphics.Dispose(); $bitmap.Dispose();"
            )

            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    command,
                ],
                capture_output=True,
                text=True,
                timeout=15,
            )

            if result.returncode != 0:
                error = result.stderr.strip()
                return (
                    "I couldn't take the screenshot. "
                    f"Error: {error}"
                )

            return (
                "Screenshot taken and saved in "
                "Pictures > Jeroo Screenshots."
            )

        except Exception as e:

            return (
                "I couldn't take the screenshot. "
                f"Error: {e}"
            )

    # =========================================
    # DATE AND TIME
    # =========================================

    def current_time(self):

        now = datetime.now()

        return now.strftime(
            "It's %I:%M %p."
        ).lstrip("0")

    def current_date(self):

        now = datetime.now()

        return now.strftime(
            "Today is %A, %d %B %Y."
        )

    # =========================================
    # SHUTDOWN
    # =========================================

    def shutdown(self):

        try:

            subprocess.Popen(
                [
                    "shutdown",
                    "/s",
                    "/t",
                    "10"
                ]
            )

            return (
                "Your PC will shut down "
                "in 10 seconds."
            )

        except Exception as e:

            return (
                f"I couldn't shut down the PC. "
                f"Error: {e}"
            )

    # =========================================
    # RESTART
    # =========================================

    def restart(self):

        try:

            subprocess.Popen(
                [
                    "shutdown",
                    "/r",
                    "/t",
                    "10"
                ]
            )

            return (
                "Your PC will restart "
                "in 10 seconds."
            )

        except Exception as e:

            return (
                f"I couldn't restart the PC. "
                f"Error: {e}"
            )

    # =========================================
    # CANCEL SHUTDOWN / RESTART
    # =========================================

    def cancel_shutdown(self):

        try:

            subprocess.run(
                [
                    "shutdown",
                    "/a"
                ],
                capture_output=True
            )

            return (
                "Shutdown or restart cancelled."
            )

        except Exception as e:

            return (
                f"I couldn't cancel the operation. "
                f"Error: {e}"
            )

    # =========================================
    # LOCK COMPUTER
    # =========================================

    def lock(self):

        try:

            subprocess.Popen(
                [
                    "rundll32.exe",
                    "user32.dll,LockWorkStation"
                ]
            )

            return "Locking your computer."

        except Exception as e:

            return (
                f"I couldn't lock the computer. "
                f"Error: {e}"
            )

    # =========================================
    # SLEEP COMPUTER
    # =========================================

    def sleep(self):

        try:

            subprocess.Popen(
                [
                    "rundll32.exe",
                    "powrprof.dll,SetSuspendState",
                    "0",
                    "1",
                    "0"
                ]
            )

            return "Putting your computer to sleep."

        except Exception as e:

            return (
                f"I couldn't put the computer "
                f"to sleep. Error: {e}"
            )
