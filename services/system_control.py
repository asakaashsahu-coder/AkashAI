import subprocess


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
                    "-Command",
                    "(New-Object -ComObject WScript.Shell).SendKeys([char]173)"
                ],
                capture_output=True
            )

            return "Audio muted."

        except Exception as e:

            return (
                f"I couldn't mute the computer. "
                f"Error: {e}"
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