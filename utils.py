import time

def log_message(app, message):
    formatted_message = f"[{time.strftime('%H:%M:%S')}] {message}"
    app.log_text.insert("end", formatted_message + "\n")
    app.log_text.see("end")
