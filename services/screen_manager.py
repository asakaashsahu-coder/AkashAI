import json
import os
import subprocess
import tempfile


class ScreenManager:

    APP_NAMES = {
        "code": "Visual Studio Code",
        "devenv": "Visual Studio",
        "chrome": "Google Chrome",
        "msedge": "Microsoft Edge",
        "firefox": "Firefox",
        "brave": "Brave",
        "opera": "Opera",
        "explorer": "File Explorer",
        "notepad": "Notepad",
        "notepad++": "Notepad++",
        "pycharm64": "PyCharm",
        "idea64": "IntelliJ IDEA",
        "powershell": "PowerShell",
        "pwsh": "PowerShell",
        "cmd": "Command Prompt",
        "windowsterminal": "Windows Terminal",
        "discord": "Discord",
        "spotify": "Spotify",
        "winword": "Microsoft Word",
        "excel": "Microsoft Excel",
        "powerpnt": "Microsoft PowerPoint",
    }

    CODE_APPS = {
        "code",
        "devenv",
        "pycharm64",
        "idea64",
        "notepad++",
    }

    BROWSER_APPS = {
        "chrome",
        "msedge",
        "firefox",
        "brave",
        "opera",
    }

    TERMINAL_APPS = {
        "powershell",
        "pwsh",
        "cmd",
        "windowsterminal",
    }

    # ==================================================
    # SCREEN CAPTURE
    # ==================================================

    def capture_screen_bytes(self):

        temp_path = None

        try:

            temp = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".png"
            )

            temp_path = temp.name
            temp.close()

            safe_path = temp_path.replace(
                "'",
                "''"
            )

            command = (
                "Add-Type -AssemblyName System.Windows.Forms; "
                "Add-Type -AssemblyName System.Drawing; "
                "$bounds = "
                "[System.Windows.Forms.SystemInformation]"
                "::VirtualScreen; "
                "$bitmap = New-Object "
                "System.Drawing.Bitmap("
                "$bounds.Width, $bounds.Height); "
                "$graphics = "
                "[System.Drawing.Graphics]"
                "::FromImage($bitmap); "
                "$graphics.CopyFromScreen("
                "$bounds.Left, "
                "$bounds.Top, "
                "0, "
                "0, "
                "$bitmap.Size); "
                f"$bitmap.Save("
                f"'{safe_path}', "
                "[System.Drawing.Imaging.ImageFormat]"
                "::Png); "
                "$graphics.Dispose(); "
                "$bitmap.Dispose();"
            )

            creation_flags = getattr(
                subprocess,
                "CREATE_NO_WINDOW",
                0
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
                timeout=20,
                creationflags=creation_flags,
            )

            if result.returncode != 0:

                error = result.stderr.strip()

                return (
                    None,
                    "I couldn't capture the screen. "
                    + (
                        error
                        or
                        "Windows returned an unknown error."
                    )
                )

            if not os.path.exists(
                temp_path
            ):

                return (
                    None,
                    "I couldn't capture the screen image."
                )

            with open(
                temp_path,
                "rb"
            ) as file:

                image_bytes = file.read()

            if not image_bytes:

                return (
                    None,
                    "The captured screen image was empty."
                )

            return (
                image_bytes,
                None
            )

        except subprocess.TimeoutExpired:

            return (
                None,
                "Screen capture timed out. "
                "Please try again."
            )

        except Exception as error:

            return (
                None,
                "I couldn't capture the screen. "
                f"Error: {error}"
            )

        finally:

            if temp_path:

                try:

                    if os.path.exists(
                        temp_path
                    ):

                        os.remove(
                            temp_path
                        )

                except OSError:
                    pass

    # ==================================================
    # ACTIVE WINDOW
    # ==================================================

    def get_active_window_info(self):

        try:

            command = r'''
Add-Type @"
using System;
using System.Text;
using System.Runtime.InteropServices;

public class JerooForeground
{
    [DllImport("user32.dll")]
    public static extern IntPtr GetForegroundWindow();

    [DllImport("user32.dll")]
    public static extern int GetWindowText(
        IntPtr hWnd,
        StringBuilder text,
        int count
    );

    [DllImport("user32.dll")]
    public static extern uint GetWindowThreadProcessId(
        IntPtr hWnd,
        out uint processId
    );
}
"@;

$hwnd = [JerooForeground]::GetForegroundWindow();

$sb = New-Object System.Text.StringBuilder 1024;

[JerooForeground]::GetWindowText(
    $hwnd,
    $sb,
    $sb.Capacity
) | Out-Null;

$pidValue = 0;

[JerooForeground]::GetWindowThreadProcessId(
    $hwnd,
    [ref]$pidValue
) | Out-Null;

$p = Get-Process -Id $pidValue -ErrorAction Stop;

[PSCustomObject]@{
    title = $sb.ToString();
    process = $p.ProcessName;
    pid = $pidValue
} | ConvertTo-Json -Compress
'''

            creation_flags = getattr(
                subprocess,
                "CREATE_NO_WINDOW",
                0
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
                creationflags=creation_flags,
            )

            if (
                result.returncode != 0
                or not result.stdout.strip()
            ):

                return None

            info = json.loads(
                result.stdout.strip()
            )

            process = str(
                info.get(
                    "process",
                    ""
                )
            ).strip()

            return {

                "title": str(
                    info.get(
                        "title",
                        ""
                    )
                ).strip(),

                "process": process,

                "pid": info.get(
                    "pid"
                ),

                "app_name": self.app_name(
                    process
                ),

                "app_type": self.app_type(
                    process
                ),
            }

        except Exception as error:

            print(
                "Active window detection error:",
                error
            )

            return None

    # ==================================================
    # FRIENDLY APP NAME
    # ==================================================

    def app_name(
        self,
        process
    ):

        process = str(
            process or ""
        ).lower().strip()

        return self.APP_NAMES.get(
            process,
            process or "Unknown app"
        )

    # ==================================================
    # APP TYPE
    # ==================================================

    def app_type(
        self,
        process
    ):

        process = str(
            process or ""
        ).lower().strip()

        if process in self.CODE_APPS:

            return "code_editor"

        if process in self.BROWSER_APPS:

            return "browser"

        if process in self.TERMINAL_APPS:

            return "terminal"

        if process == "explorer":

            return "file_manager"

        return "general"

    # ==================================================
    # COMPARE WINDOWS
    # ==================================================

    def same_window(
        self,
        first,
        second
    ):

        if (
            not first
            or not second
        ):

            return False

        first_process = str(
            first.get(
                "process"
            )
            or ""
        ).lower().strip()

        second_process = str(
            second.get(
                "process"
            )
            or ""
        ).lower().strip()

        first_title = str(
            first.get(
                "title"
            )
            or ""
        ).lower().strip()

        second_title = str(
            second.get(
                "title"
            )
            or ""
        ).lower().strip()

        return (
            first_process
            == second_process

            and

            first_title
            == second_title
        )