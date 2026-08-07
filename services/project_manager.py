import os
import subprocess


class ProjectManager:

    def __init__(self):

        self.projects = {
            "akashai": os.path.abspath(
                os.path.join(
                    os.path.dirname(
                        os.path.dirname(__file__)
                    )
                )
            )
        }

        self.folders = {
            "desktop": os.path.join(
                os.path.expanduser("~"),
                "Desktop"
            ),

            "downloads": os.path.join(
                os.path.expanduser("~"),
                "Downloads"
            ),

            "documents": os.path.join(
                os.path.expanduser("~"),
                "Documents"
            ),

            "pictures": os.path.join(
                os.path.expanduser("~"),
                "Pictures"
            ),

            "music": os.path.join(
                os.path.expanduser("~"),
                "Music"
            ),

            "videos": os.path.join(
                os.path.expanduser("~"),
                "Videos"
            ),
        }

    # -----------------------------------------
    # OPEN PROJECT
    # -----------------------------------------

    def open_project(self, project_name):

        project_name = project_name.lower().strip()

        if project_name not in self.projects:

            return (
                f"I don't know the project "
                f"{project_name} yet."
            )

        path = self.projects[project_name]

        if not os.path.isdir(path):

            return (
                f"I couldn't find the project folder:\n"
                f"{path}"
            )

        try:

            os.startfile(path)

            try:

                subprocess.Popen(
                    [
                        "code.cmd",
                        path
                    ],
                    shell=True
                )

            except Exception as e:

                print(
                    "VS Code launch error:",
                    e
                )

            return (
                "Opening your AKASHAI project."
            )

        except Exception as e:

            return (
                f"I couldn't open the project.\n"
                f"Error: {e}"
            )

    # -----------------------------------------
    # OPEN COMMON FOLDER
    # -----------------------------------------

    def open_folder(self, folder_name):

        folder_name = folder_name.lower().strip()

        if folder_name not in self.folders:

            return (
                f"I don't know the folder "
                f"{folder_name} yet."
            )

        path = self.folders[folder_name]

        if not os.path.isdir(path):

            return (
                f"I couldn't find:\n{path}"
            )

        try:

            os.startfile(path)

            return (
                f"Opening {folder_name}."
            )

        except Exception as e:

            return (
                f"I couldn't open {folder_name}.\n"
                f"Error: {e}"
            )