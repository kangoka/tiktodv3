import tkinter as tk
import customtkinter as ctk
import threading
import time
from PIL import Image  # Import the Image class
from bot import Bot
from utils import log_message, resource_path

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("TIKTOD V3")
        self.geometry("800x600")
        self.iconbitmap(resource_path("assets/logo.ico"))

        # Configure grid layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Create sidebar frame with widgets
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color="gray20")
        self.sidebar_frame.grid(row=0, column=0, rowspan=5, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(9, weight=1)

        custom_font = ctk.CTkFont(family="Helvetica", size=14, weight="bold")

        self.logo_image_dark = ctk.CTkImage(light_image=Image.open(resource_path("assets/dark-logo.png")), size=(100, 100))
        self.logo_image_light = ctk.CTkImage(light_image=Image.open(resource_path("assets/light-logo.png")), size=(100, 100))
        self.logo_image_label = ctk.CTkLabel(self.sidebar_frame, image=self.logo_image_dark, text="")
        self.logo_image_label.grid(row=0, column=0, padx=20, pady=(20, 20))

        self.link_label = ctk.CTkLabel(self.sidebar_frame, text="TikTok video URL:", font=custom_font, anchor="w")  # Added anchor="w"
        self.link_label.grid(row=1, column=0, padx=20, pady=1, sticky="w")  # Added sticky="w"
        self.link_entry = ctk.CTkEntry(self.sidebar_frame, width=180, font=custom_font)
        self.link_entry.grid(row=2, column=0, padx=20, pady=1)

        self.amount_label = ctk.CTkLabel(self.sidebar_frame, text="Amount:", font=custom_font, anchor="w")  # New label
        self.amount_label.grid(row=3, column=0, padx=20, pady=1, sticky="w")  # New label grid
        self.amount_entry = ctk.CTkEntry(self.sidebar_frame, width=180, font=custom_font)  # New entry
        self.amount_entry.grid(row=4, column=0, padx=20, pady=1)  # New entry grid

        self.start_button = ctk.CTkButton(self.sidebar_frame, text="Setup", command=lambda: threading.Thread(target=self.setup_bot).start(), font=custom_font)
        self.start_button.grid(row=6, column=0, padx=20, pady=20)  # Adjusted row to move the button lower

        # Create main frame with tab view for log and stats
        self.main_frame = ctk.CTkFrame(self, corner_radius=0)
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        self.tab_view = ctk.CTkTabview(self.main_frame)
        self.tab_view.grid(row=0, column=0, padx=20, pady=10, sticky="nsew")

        self.log_tab = self.tab_view.add("Log")
        self.log_text = ctk.CTkTextbox(self.log_tab, height=300, width=600, font=custom_font)
        self.log_text.pack(padx=20, pady=10, fill="both", expand=True)

        self.stats_tab = self.tab_view.add("Stats")
        self.stats_tab.grid_rowconfigure(0, weight=1)
        self.stats_tab.grid_columnconfigure(0, weight=1)

        self.stats_frame = ctk.CTkFrame(self.stats_tab)
        self.stats_frame.grid(row=0, column=0, padx=20, pady=10, sticky="nsew")

        self.stats_labels = {
            "views": ctk.CTkLabel(self.stats_frame, text="Views Sent: 0", font=custom_font),
            "hearts": ctk.CTkLabel(self.stats_frame, text="Hearts Sent: 0", font=custom_font),
            "followers": ctk.CTkLabel(self.stats_frame, text="Followers Sent: 0", font=custom_font),
            "shares": ctk.CTkLabel(self.stats_frame, text="Shares Sent: 0", font=custom_font),
            "favorites": ctk.CTkLabel(self.stats_frame, text="Favorites Sent: 0", font=custom_font),
            "elapsed_time": ctk.CTkLabel(self.stats_frame, text="Elapsed Time: 00:00:00", font=custom_font)
        }

        for i, label in enumerate(self.stats_labels.values()):
            label.grid(row=i, column=0, padx=20, pady=5, sticky="w")

        self.running = False  # Add a flag to control the loop
        self.mode_var = tk.StringVar(value="Views")  # Initialize mode_var
        self.bot = Bot(self, log_message)
        self.elapsed_time = 0  # Initialize elapsed_time
        self.views = 0  # Initialize views
        self.hearts = 0  # Initialize hearts
        self.followers = 0  # Initialize followers
        self.shares = 0  # Initialize shares
        self.favorites = 0  # Initialize favorites

        self.theme_switch_var = tk.StringVar(value="dark")
        self.theme_switch = ctk.CTkSwitch(self.sidebar_frame, text="Dark Mode", variable=self.theme_switch_var, onvalue="dark", offvalue="light", command=self.switch_theme, font=custom_font)
        self.theme_switch.grid(row=10, column=0, padx=20, pady=10, sticky="s")

        self.version_label = ctk.CTkLabel(self, text="Version 1.1.0", fg_color="transparent")
        self.version_label.grid(row=5, column=1, padx=20, pady=(10, 0), sticky="se")

        self.github_link = ctk.CTkLabel(self, text="https://github.com/kangoka/tiktodv3", fg_color="transparent", cursor="hand2")
        self.github_link.grid(row=6, column=1, padx=20, pady=(0, 10), sticky="se")
        self.github_link.bind("<Button-1>", lambda e: self.open_github())

    def open_github(self):
        import webbrowser
        webbrowser.open("https://github.com/kangoka/tiktodv3")

    def switch_theme(self):
        if self.theme_switch_var.get() == "dark":
            ctk.set_appearance_mode("dark")
            self.sidebar_frame.configure(fg_color="gray20")
            self.logo_image_label.configure(image=self.logo_image_dark)
        else:
            ctk.set_appearance_mode("light")
            self.sidebar_frame.configure(fg_color="white")
            self.logo_image_label.configure(image=self.logo_image_light)

    def setup_bot(self):
        self.bot.setup_bot()

    def start_bot(self):
        auto = self.mode_var.get()
        vidUrl = self.link_entry.get()
        
        try:
            amount = int(self.amount_entry.get())  # Get the amount entered and ensure it is a number
        except ValueError:
            log_message(self, "Amount must be a number")
            return

        if auto in ["Views", "Hearts", "Followers", "Shares", "Favorites"]:
            if not self.running:
                self.start_time = time.time() - self.elapsed_time  # Continue from the last elapsed time
                self.log_text.delete(1.0, tk.END)  # Clear the log area
                log_message(self, "TIKTOD V3")
                log_message(self, "Log:")

            self.running = True  # Set the flag to True
            self.bot.running = True  # Ensure the bot's running flag is also set to True

            self.link_entry.configure(state="disabled")  # Disable the URL entry
            self.amount_entry.configure(state="disabled")  # Disable the amount entry
            self.mode_menu.configure(state="disabled")  # Disable the option menu

            threading.Thread(target=self.update_stats_label).start()  # Start the stats update thread

            threading.Thread(target=self.bot.loop, args=(vidUrl, auto, amount)).start()  # Pass the amount to the bot loop
            
            self.start_button.configure(text="Stop", command=self.stop_bot)
        else:
            log_message(self, f"{auto} is not a valid option. Please pick Views, Hearts, Followers, Shares, or Favorites")

    def stop_bot(self):
        log_message(self, "Bot stopped")

        self.link_entry.configure(state="normal")  # Enable the URL entry
        self.amount_entry.configure(state="normal")  # Enable the amount entry
        self.mode_menu.configure(state="normal")  # Enable the option menu

        self.running = False  # Set the flag to False
        self.bot.running = False  # Ensure the bot's running flag is also set to False
        self.elapsed_time = time.time() - self.start_time  # Save the elapsed time

        self.start_button.configure(text="Start", command=self.start_bot)

    def update_stats_label(self):
        while self.running:
            time_elapsed = time.strftime('%H:%M:%S', time.gmtime(time.time() - self.start_time))
            self.stats_labels["elapsed_time"].configure(text=f"Elapsed Time: {time_elapsed}")
            self.stats_labels["views"].configure(text=f"Views Sent: {self.views}")
            self.stats_labels["hearts"].configure(text=f"Hearts Sent: {self.hearts}")
            self.stats_labels["followers"].configure(text=f"Followers Sent: {self.followers}")
            self.stats_labels["shares"].configure(text=f"Shares Sent: {self.shares}")
            self.stats_labels["favorites"].configure(text=f"Favorites Sent: {self.favorites}")
            time.sleep(1)

if __name__ == "__main__":
    app = App()
    app.mainloop()
