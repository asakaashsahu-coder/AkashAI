import os
import shutil


class AppScanner:

    def __init__(self):

        self.apps = {}

    # --------------------------------------------------
    # SCAN WINDOWS START MENU
    # --------------------------------------------------

    def scan_start_menu(self):

        start_menu_paths = [

            r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs",

            os.path.join(
                os.path.expanduser("~"),
                r"AppData\Roaming\Microsoft\Windows\Start Menu\Programs"
            )

        ]

        for folder in start_menu_paths:

            if not os.path.exists(folder):
                continue

            for root, dirs, files in os.walk(folder):

                for file in files:

                    if file.lower().endswith(".lnk"):

                        name = os.path.splitext(
                            file
                        )[0].lower().strip()

                        self.apps[name] = os.path.join(
                            root,
                            file
                        )

    # --------------------------------------------------
    # SCAN PROGRAMS AVAILABLE THROUGH PATH
    # --------------------------------------------------

    def scan_path_commands(self):

        common_apps = [

            "spotify",
            "discord",
            "steam",
            "telegram",
            "whatsapp",
            "code",
            "chrome",
            "msedge",
            "firefox",
            "notepad",
            "calc",
            "mspaint",
            "powershell",
            "cmd",
        ]

        for app in common_apps:

            executable = shutil.which(
                app
            )

            if executable:

                name = app.lower()

                if name not in self.apps:

                    self.apps[name] = executable

    # --------------------------------------------------
    # FULL SCAN
    # --------------------------------------------------

    def scan(self):

        self.apps.clear()

        # Start Menu applications
        self.scan_start_menu()

        # PATH applications
        self.scan_path_commands()

        return self.apps