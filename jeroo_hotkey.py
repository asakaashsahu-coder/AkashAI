import keyboard
import subprocess
import sys
import os


# ==========================================
# JEROO LOCATION
# ==========================================

APP_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

APP_FILE = os.path.join(
    APP_DIR,
    "app.py"
)

PYTHON_EXE = sys.executable


# ==========================================
# CHECK IF JEROO APP IS RUNNING
# ==========================================

def is_jeroo_running():

    try:

        result = subprocess.run(
            [
                "wmic",
                "process",
                "where",
                "name='python.exe'",
                "get",
                "commandline"
            ],
            capture_output=True,
            text=True
        )

        output = result.stdout.lower()

        app_path = APP_FILE.lower()

        return app_path in output

    except Exception as e:

        print(
            "Process check error:",
            e
        )

        return False


# ==========================================
# LAUNCH JEROO
# ==========================================

def launch_jeroo():

    print(
        "🚀 Launching Jeroo..."
    )

    try:

        subprocess.Popen(
            [
                PYTHON_EXE,
                APP_FILE
            ],
            cwd=APP_DIR
        )

        print(
            "Jeroo launched successfully."
        )

    except Exception as e:

        print(
            "Launch error:",
            e
        )


# ==========================================
# GLOBAL HOTKEY
# ==========================================

def toggle_jeroo():

    print(
        "\nCtrl + Shift + J pressed"
    )

    if is_jeroo_running():

        print(
            "Jeroo is already running."
        )

        return

    launch_jeroo()


# ==========================================
# REGISTER HOTKEY
# ==========================================

keyboard.add_hotkey(
    "ctrl+shift+j",
    toggle_jeroo
)


print(
    "===================================="
)

print(
    "Jeroo Global Launcher"
)

print(
    "Shortcut: Ctrl + Shift + J"
)

print(
    "Waiting for shortcut..."
)

print(
    "===================================="
)


# ==========================================
# KEEP LAUNCHER RUNNING
# ==========================================

keyboard.wait()