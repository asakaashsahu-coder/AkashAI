
import keyboard
import subprocess
import sys
import os
import threading

from gui.main_window import MainWindow


APP_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

APP_FILE = os.path.join(
    APP_DIR,
    "app.py"
)


def main():

    print("Starting AkashAI...\n")

    app = MainWindow()

    print("Window created...\n")

    # ==========================================
    # BRING JEROO TO FRONT
    # ==========================================

    def show_jeroo():

        try:

            app.after(
                0,
                bring_to_front
            )

        except Exception as e:

            print(
                "Window error:",
                e
            )

    def bring_to_front():

        try:

            app.deiconify()

            app.lift()

            app.attributes(
                "-topmost",
                True
            )

            app.after(
                300,
                lambda: app.attributes(
                    "-topmost",
                    False
                )
            )

            app.focus_force()

        except Exception as e:

            print(
                "Bring to front error:",
                e
            )

    # ==========================================
    # GLOBAL SHORTCUT
    # ==========================================

    keyboard.add_hotkey(
        "ctrl+shift+j",
        show_jeroo
    )

    print(
        "Global shortcut enabled: "
        "Ctrl + Shift + J\n"
    )

    # ==========================================
    # START APPLICATION
    # ==========================================

    try:

        app.mainloop()

    finally:

        keyboard.unhook_all()


if __name__ == "__main__":

    main()

