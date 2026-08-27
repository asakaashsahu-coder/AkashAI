
import keyboard
import subprocess
import sys
import os
import threading

from gui.main_window import MainWindow
from services.startup_manager import StartupManager


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

    startup_manager = StartupManager()

    startup_ok, startup_message = startup_manager.enable()

    if startup_ok:
        print(
            "Windows startup enabled for Jerro."
        )
    else:
        print(
            startup_message
        )

    start_as_orb = (
        "--orb" in sys.argv
    )

    if start_as_orb:
        try:
            app.withdraw()
        except Exception:
            pass

        app.after(
            180,
            app.start_in_floating_mode
        )

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

            app.restore_full_window()

        except Exception as e:

            print(
                "Bring to front error:",
                e
            )

    # ==========================================
    # GLOBAL SHORTCUT
    # ==========================================

    hotkey_registered = False

    try:
        keyboard.add_hotkey(
            "ctrl+shift+j",
            show_jeroo
        )

        hotkey_registered = True

        print(
            "Global shortcut enabled: "
            "Ctrl + Shift + J\n"
        )

    except Exception as error:
        print(
            "Global shortcut unavailable:",
            error
        )

    # ==========================================
    # START APPLICATION
    # ==========================================

    try:

        app.mainloop()

    finally:

        if hotkey_registered:
            try:
                keyboard.unhook_all()
            except Exception:
                pass


if __name__ == "__main__":

    main()

