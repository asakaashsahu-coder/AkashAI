import os


class AppScanner:

    def __init__(self):

        self.apps = {}

    def scan(self):

        start_menu_paths = [
            r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs",
            os.path.join(
                os.path.expanduser("~"),
                r"AppData\Roaming\Microsoft\Windows\Start Menu\Programs"
            )
        ]

        self.apps.clear()

        for folder in start_menu_paths:

            if not os.path.exists(folder):
                continue

            for root, dirs, files in os.walk(folder):

                for file in files:

                    if file.endswith(".lnk"):

                        name = os.path.splitext(file)[0].lower()

                        self.apps[name] = os.path.join(root, file)

        return self.apps