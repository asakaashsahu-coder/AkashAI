import os
import subprocess
import tempfile


class ScreenManager:

    def capture_screen_bytes(self):
        """
        Capture the full Windows virtual desktop into a temporary PNG,
        return its bytes, then remove the temporary file.
        """

        temp_path = None

        try:
            temp = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".png"
            )
            temp_path = temp.name
            temp.close()

            safe_path = temp_path.replace("'", "''")

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
                return None, (
                    "I couldn't capture the screen. "
                    + (error or "Windows returned an unknown error.")
                )

            if not os.path.exists(temp_path):
                return None, "I couldn't capture the screen image."

            with open(temp_path, "rb") as file:
                image_bytes = file.read()

            if not image_bytes:
                return None, "The captured screen image was empty."

            return image_bytes, None

        except subprocess.TimeoutExpired:
            return None, "Screen capture timed out. Please try again."

        except Exception as e:
            return None, f"I couldn't capture the screen. Error: {e}"

        finally:
            if temp_path:
                try:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                except OSError:
                    pass

    def get_active_window_info(self):
        """Return the current foreground Windows app/process and title."""
        try:
            command = r'''Add-Type @"
using System;
using System.Text;
using System.Runtime.InteropServices;
public class JerooForeground {
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] public static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);
}
"@;
$hwnd=[JerooForeground]::GetForegroundWindow();
$sb=New-Object System.Text.StringBuilder 1024;
[JerooForeground]::GetWindowText($hwnd,$sb,$sb.Capacity) | Out-Null;
$pidValue=0;
[JerooForeground]::GetWindowThreadProcessId($hwnd,[ref]$pidValue) | Out-Null;
$p=Get-Process -Id $pidValue -ErrorAction Stop;
[PSCustomObject]@{title=$sb.ToString(); process=$p.ProcessName; pid=$pidValue} | ConvertTo-Json -Compress'''
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", command],
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            if result.returncode != 0 or not result.stdout.strip():
                return None
            import json
            info = json.loads(result.stdout.strip())
            return {
                "title": str(info.get("title", "")).strip(),
                "process": str(info.get("process", "")).strip(),
                "pid": info.get("pid"),
            }
        except Exception as e:
            print("Active window detection error:", e)
            return None
