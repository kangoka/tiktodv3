import tkinter as tk
import customtkinter as ctk
import threading
import time
from bot import Bot
from utils import log_message

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("TIKTOD V3")
        self.geometry("800x600")

        # Configure grid layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Create sidebar frame with widgets
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color="gray20")
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(8, weight=1)

        custom_font = ctk.CTkFont(family="Helvetica", size=14, weight="bold")

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="TIKTOD V3", font=ctk.CTkFont(family="Helvetica", size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.link_label = ctk.CTkLabel(self.sidebar_frame, text="TikTok video URL:", font=custom_font)
        self.link_label.grid(row=1, column=0, padx=20, pady=10)
        self.link_entry = ctk.CTkEntry(self.sidebar_frame, width=180, font=custom_font)
        self.link_entry.grid(row=2, column=0, padx=20, pady=5)

        self.start_button = ctk.CTkButton(self.sidebar_frame, text="Setup", command=lambda: threading.Thread(target=self.setup_bot).start(), font=custom_font)
        self.start_button.grid(row=3, column=0, padx=20, pady=20)

        self.theme_switch_var = tk.StringVar(value="dark")
        self.theme_switch = ctk.CTkSwitch(self.sidebar_frame, text="Dark Mode", variable=self.theme_switch_var, onvalue="dark", offvalue="light", command=self.switch_theme, font=custom_font)
        self.theme_switch.grid(row=4, column=0, padx=20, pady=10)

        # Create main frame for log and stats
        self.main_frame = ctk.CTkFrame(self, corner_radius=0)
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        self.log_text = ctk.CTkTextbox(self.main_frame, height=300, width=600, font=custom_font)
        self.log_text.grid(row=0, column=0, padx=20, pady=10, sticky="nsew")

        self.stats_label = ctk.CTkLabel(self.main_frame, text="TIKTOD V3 | Ready | Elapsed Time: 00:00:00", font=custom_font)
        self.stats_label.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        self.running = False  # Add a flag to control the loop
        self.mode_var = tk.StringVar(value="Views")  # Initialize mode_var
        self.bot = Bot(self, log_message)

    def switch_theme(self):
        if self.theme_switch_var.get() == "dark":
            ctk.set_appearance_mode("dark")
            self.sidebar_frame.configure(fg_color="gray20")
        else:
            ctk.set_appearance_mode("light")
            self.sidebar_frame.configure(fg_color="white")

    def setup_bot(self):
        self.bot.setup_bot()

    def start_bot(self):
        auto = self.mode_var.get()
        vidUrl = self.link_entry.get()

        if auto in ["Views", "Hearts", "Followers", "Shares"]:
            self.start_time = time.time()
            self.views = 0
            self.hearts = 0
            self.followers = 0
            self.shares = 0

            self.log_text.delete(1.0, tk.END)  # Clear the log area
            log_message(self, "TIKTOD V3")
            log_message(self, "Log:")

            self.running = True  # Set the flag to True
            self.bot.running = True  # Ensure the bot's running flag is also set to True

            if auto == "Views":
                threading.Thread(target=self.update_stats_label, args=(1,)).start()
                threading.Thread(target=self.bot.loop, args=(vidUrl, "Views")).start()
            elif auto == "Hearts":
                threading.Thread(target=self.update_stats_label, args=(2,)).start()
                threading.Thread(target=self.bot.loop, args=(vidUrl, "Hearts")).start()
            elif auto == "Followers":
                threading.Thread(target=self.update_stats_label, args=(3,)).start()
                threading.Thread(target=self.bot.loop, args=(vidUrl, "Followers")).start()
            elif auto == "Shares":
                threading.Thread(target=self.update_stats_label, args=(4,)).start()
                threading.Thread(target=self.bot.loop, args=(vidUrl, "Shares")).start()
            
            self.start_button.configure(text="Stop", command=self.stop_bot)
        else:
            log_message(self, f"{auto} is not a valid option. Please pick Views, Hearts, Followers, or Shares")

    def stop_bot(self):
        log_message(self, "Stop button pressed")
        self.running = False  # Set the flag to False
        self.bot.running = False  # Ensure the bot's running flag is also set to False
        self.start_button.configure(text="Start", command=self.start_bot)

    def update_stats_label(self, mode):
        while self.running:
            time_elapsed = time.strftime('%H:%M:%S', time.gmtime(time.time() - self.start_time))
            if mode == 1:
                self.stats_label.configure(text=f"TIKTOD V3 | Views Sent: {self.views} | Elapsed Time: {time_elapsed}")
            elif mode == 2:
                self.stats_label.configure(text=f"TIKTOD V3 | Hearts Sent: {self.hearts} | Elapsed Time: {time_elapsed}")
            elif mode == 3:
                self.stats_label.configure(text=f"TIKTOD V3 | Followers Sent: {self.followers} | Elapsed Time: {time_elapsed}")
            elif mode == 4:
                self.stats_label.configure(text=f"TIKTOD V3 | Shares Sent: {self.shares} | Elapsed Time: {time_elapsed}")
            time.sleep(1)

if __name__ == "__main__":
    app = App()
    app.mainloop()
