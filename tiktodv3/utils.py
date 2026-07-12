import os
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def log_message(app, message: str) -> None:
    formatted_message = f"[{time.strftime('%H:%M:%S')}] {message}"
    native_textbox = getattr(app.log_text, "_textbox", app.log_text)
    previous_state = native_textbox.cget("state")
    if previous_state == "disabled":
        app.log_text.configure(state="normal")
    app.log_text.insert("end", formatted_message + "\n")
    app.log_text.see("end")
    if previous_state == "disabled":
        app.log_text.configure(state="disabled")


def resource_path(relative_path: str) -> str:
    if hasattr(sys, "_MEIPASS"):
        base_path = Path(sys._MEIPASS)
    else:
        base_path = PROJECT_ROOT
    return os.fspath(base_path / relative_path)
