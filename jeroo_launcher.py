import os
import sys
import subprocess
import time
import tkinter as tk


APP_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

APP_FILE = os.path.join(
    APP_DIR,
    "app.py"
)


def launch_jeroo():

    python_exe = sys.executable

    subprocess.Popen(
        [
            python_exe,
            APP_FILE
        ],
        cwd=APP_DIR
    )


if __name__ == "__main__":

    launch_jeroo()