import subprocess
from datetime import datetime
from pathlib import Path


class SystemControl:

    def _powershell(self, command, timeout=10):

        return subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                command,
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
            creationflags=getattr(
                subprocess,
                "CREATE_NO_WINDOW",
                0
            ),
        )

    def _send_keys(self, keys):

        try:

            safe_keys = str(keys).replace(
                "'",
                "''"
            )

            result = self._powershell(
                "(New-Object -ComObject WScript.Shell)"
                f".SendKeys('{safe_keys}')"
            )

            return result.returncode == 0

        except Exception:

            return False

    # ==================================================
    # VOLUME
    # ==================================================

    def volume_up(self):

        try:

            for _ in range(5):

                self._powershell(
                    "(New-Object -ComObject WScript.Shell)"
                    ".SendKeys([char]175)"
                )

            return "Volume increased."

        except Exception as error:

            return (
                "I couldn't increase the volume. "
                f"Error: {error}"
            )

    def volume_down(self):

        try:

            for _ in range(5):

                self._powershell(
                    "(New-Object -ComObject WScript.Shell)"
                    ".SendKeys([char]174)"
                )

            return "Volume decreased."

        except Exception as error:

            return (
                "I couldn't decrease the volume. "
                f"Error: {error}"
            )

    def mute(self):

        try:

            self._powershell(
                "(New-Object -ComObject WScript.Shell)"
                ".SendKeys([char]173)"
            )

            return "Audio mute toggled."

        except Exception as error:

            return (
                "I couldn't change the mute state. "
                f"Error: {error}"
            )

    # ==================================================
    # MEDIA CONTROLS
    # ==================================================

    def media_play_pause(self):

        try:

            self._powershell(
                "(New-Object -ComObject WScript.Shell)"
                ".SendKeys([char]179)"
            )

            return "Play/pause toggled."

        except Exception as error:

            return (
                "I couldn't control playback. "
                f"Error: {error}"
            )

    def media_next(self):

        try:

            self._powershell(
                "(New-Object -ComObject WScript.Shell)"
                ".SendKeys([char]176)"
            )

            return "Skipped to the next track."

        except Exception as error:

            return (
                "I couldn't skip the track. "
                f"Error: {error}"
            )

    def media_previous(self):

        try:

            self._powershell(
                "(New-Object -ComObject WScript.Shell)"
                ".SendKeys([char]177)"
            )

            return "Went back to the previous track."

        except Exception as error:

            return (
                "I couldn't go to the previous track. "
                f"Error: {error}"
            )

    # ==================================================
    # BROWSER CONTROLS
    # ==================================================

    def browser_new_tab(self):

        if self._send_keys("^t"):

            return "Opened a new tab."

        return "I couldn't open a new tab."

    def browser_close_tab(self):

        if self._send_keys("^w"):

            return "Closed the current tab."

        return "I couldn't close the current tab."

    def browser_reopen_tab(self):

        if self._send_keys("^+t"):

            return "Reopened the last closed tab."

        return "I couldn't reopen the last closed tab."

    def browser_refresh(self):

        if self._send_keys("^r"):

            return "Refreshed the current page."

        return "I couldn't refresh the page."

    def browser_back(self):

        if self._send_keys("%{LEFT}"):

            return "Went back one page."

        return "I couldn't go back."

    def browser_forward(self):

        if self._send_keys("%{RIGHT}"):

            return "Went forward one page."

        return "I couldn't go forward."

    def browser_focus_address_bar(self):

        if self._send_keys("^l"):

            return "Focused the address bar."

        return "I couldn't focus the address bar."

    def find_on_page(self):

        if self._send_keys("^f"):

            return "Opened Find on this page."

        return "I couldn't open Find."

    # ==================================================
    # ACTIVE WINDOW MANAGEMENT
    # ==================================================

    def _show_active_window(
        self,
        show_code
    ):

        try:

            command = f'''
Add-Type @"
using System;
using System.Runtime.InteropServices;

public class JerroWindowControl
{{
    [DllImport("user32.dll")]
    public static extern IntPtr GetForegroundWindow();

    [DllImport("user32.dll")]
    public static extern bool ShowWindow(
        IntPtr hWnd,
        int nCmdShow
    );
}}
"@;

$hwnd = [JerroWindowControl]::GetForegroundWindow();

if ($hwnd -eq [IntPtr]::Zero)
{{
    exit 1
}}

[JerroWindowControl]::ShowWindow(
    $hwnd,
    {show_code}
) | Out-Null
'''

            result = self._powershell(
                command
            )

            return result.returncode == 0

        except Exception:

            return False

    def minimize_current_window(self):

        if self._show_active_window(6):

            return "Minimized the current window."

        return (
            "I couldn't minimize "
            "the current window."
        )

    def maximize_current_window(self):

        if self._show_active_window(3):

            return "Maximized the current window."

        return (
            "I couldn't maximize "
            "the current window."
        )

    def restore_current_window(self):

        if self._show_active_window(9):

            return "Restored the current window."

        return (
            "I couldn't restore "
            "the current window."
        )

    # ==================================================
    # BATTERY STATUS
    # ==================================================

    def battery_status(self):

        try:

            command = (
                "$battery = "
                "Get-CimInstance Win32_Battery | "
                "Select-Object -First 1; "

                "if ($null -eq $battery) "
                "{ "
                "Write-Output 'NO_BATTERY' "
                "} "
                "else "
                "{ "
                "Write-Output "
                "($battery."
                "EstimatedChargeRemaining."
                "ToString() + '|' + "
                "$battery."
                "BatteryStatus."
                "ToString()) "
                "}"
            )

            result = self._powershell(
                command,
                timeout=10
            )

            output = (
                result.stdout.strip()
            )

            if (
                not output
                or output == "NO_BATTERY"
            ):

                return (
                    "I couldn't detect a battery "
                    "on this computer."
                )

            percentage, status_code = (
                output.split(
                    "|",
                    1
                )
            )

            status_names = {

                "1": "discharging",

                "2":
                    "connected to power",

                "3":
                    "fully charged",

                "4": "low",

                "5": "critical",

                "6": "charging",

                "7": "charging",

                "8": "charging",

                "9": "charging",

                "10": "undefined",

                "11":
                    "partially charged",
            }

            state = status_names.get(
                status_code.strip(),
                "status unknown"
            )

            return (
                f"Your battery is at "
                f"{percentage}% "
                f"and is {state}."
            )

        except Exception as error:

            return (
                "I couldn't read the "
                "battery status. "
                f"Error: {error}"
            )

    # ==================================================
    # SCREENSHOT
    # ==================================================

    def take_screenshot(self):

        try:

            pictures = (
                Path.home()
                / "Pictures"
            )

            screenshot_folder = (
                pictures
                / "Jeroo Screenshots"
            )

            screenshot_folder.mkdir(
                parents=True,
                exist_ok=True
            )

            timestamp = (
                datetime.now().strftime(
                    "%Y-%m-%d_%H-%M-%S"
                )
            )

            screenshot_path = (
                screenshot_folder
                / (
                    "Jeroo_Screenshot_"
                    f"{timestamp}.png"
                )
            )

            safe_path = (
                str(
                    screenshot_path
                ).replace(
                    "'",
                    "''"
                )
            )

            command = (
                "Add-Type -AssemblyName "
                "System.Windows.Forms; "

                "Add-Type -AssemblyName "
                "System.Drawing; "

                "$bounds = "
                "[System.Windows.Forms."
                "SystemInformation]"
                "::VirtualScreen; "

                "$bitmap = New-Object "
                "System.Drawing.Bitmap"
                "($bounds.Width, "
                "$bounds.Height); "

                "$graphics = "
                "[System.Drawing.Graphics]"
                "::FromImage($bitmap); "

                "$graphics.CopyFromScreen"
                "($bounds.Left, "
                "$bounds.Top, "
                "0, "
                "0, "
                "$bitmap.Size); "

                f"$bitmap.Save("
                f"'{safe_path}', "
                "[System.Drawing.Imaging."
                "ImageFormat]::Png); "

                "$graphics.Dispose(); "
                "$bitmap.Dispose();"
            )

            result = self._powershell(
                command,
                timeout=15
            )

            if result.returncode != 0:

                error = (
                    result.stderr.strip()
                )

                return (
                    "I couldn't take "
                    "the screenshot. "
                    f"Error: {error}"
                )

            return (
                "Screenshot taken and saved in "
                "Pictures > Jeroo Screenshots."
            )

        except Exception as error:

            return (
                "I couldn't take "
                "the screenshot. "
                f"Error: {error}"
            )

    # ==================================================
    # DATE AND TIME
    # ==================================================

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

    # ==================================================
    # SHUTDOWN
    # ==================================================

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

        except Exception as error:

            return (
                "I couldn't shut down the PC. "
                f"Error: {error}"
            )

    # ==================================================
    # RESTART
    # ==================================================

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

        except Exception as error:

            return (
                "I couldn't restart the PC. "
                f"Error: {error}"
            )

    # ==================================================
    # CANCEL SHUTDOWN / RESTART
    # ==================================================

    def cancel_shutdown(self):

        try:

            subprocess.run(
                [
                    "shutdown",
                    "/a"
                ],
                capture_output=True,
                creationflags=getattr(
                    subprocess,
                    "CREATE_NO_WINDOW",
                    0
                ),
            )

            return (
                "Shutdown or restart cancelled."
            )

        except Exception as error:

            return (
                "I couldn't cancel the operation. "
                f"Error: {error}"
            )

    # ==================================================
    # LOCK COMPUTER
    # ==================================================

    def lock(self):

        try:

            subprocess.Popen(
                [
                    "rundll32.exe",
                    "user32.dll,LockWorkStation"
                ]
            )

            return (
                "Locking your computer."
            )

        except Exception as error:

            return (
                "I couldn't lock the computer. "
                f"Error: {error}"
            )

    # ==================================================
    # SLEEP COMPUTER
    # ==================================================

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

            return (
                "Putting your computer to sleep."
            )

        except Exception as error:

            return (
                "I couldn't put the computer "
                f"to sleep. Error: {error}"
            )