import time
import os
import sys

def log_message(app, message):
    formatted_message = f"[{time.strftime('%H:%M:%S')}] {message}"
    try:
        # Thread-safe way to update GUI from any thread
        app.log_text.after(0, lambda: app.log_text.insert("end", formatted_message + "\n"))
        app.log_text.after(0, app.log_text.see, "end")
    except Exception as e:
        # Fallback: just print to console if GUI update fails
        print(formatted_message)

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)
