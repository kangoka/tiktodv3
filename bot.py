import chromedriver_autoinstaller
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
import pytesseract
import time
import random
import customtkinter as ctk
import tkinter as tk
import re
from utils import log_message, resource_path

class Bot:
    def __init__(self, app, log_callback):
        self.app = app
        self.log_callback = log_callback
        self.driver = None
        self.running = False

    def setup_bot(self):
        log_message(self.app, "Setting up the bot...")
        # Automatically install the correct version of ChromeDriver
        chromedriver_autoinstaller.install()
        
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Enable headless mode
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-webgl")
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_argument("--log-level=3")  # Suppress most logs
        chrome_options.add_argument("--disable-logging")  # Disable logging
        
        self.driver = webdriver.Chrome(options=chrome_options)

        # Block requests to fundingchoicesmessages.google.com
        self.driver.execute_cdp_cmd(
            "Network.setBlockedURLs",
            {"urls": ["https://fundingchoicesmessages.google.com/*"]}
        )
        self.driver.execute_cdp_cmd("Network.enable", {})  # Enable network interception

        self.get_captcha()

        # Create a frame for the mode selection
        self.app.mode_frame = ctk.CTkFrame(self.app.sidebar_frame, corner_radius=0)
        self.app.mode_frame.grid(row=5, column=0, padx=20, pady=10, sticky="nsew")

        self.app.mode_label = ctk.CTkLabel(self.app.mode_frame, text="Select Mode:")
        self.app.mode_label.grid(row=0, column=0, padx=20, pady=10)
        self.app.mode_var = tk.StringVar(value="----------")

        available_modes = []
        buttons = {
            "Followers": '//button[@class="btn btn-primary rounded-0 t-followers-button"]',
            "Hearts": '//button[@class="btn btn-primary rounded-0 t-hearts-button"]',
            "Views": '//button[@class="btn btn-primary rounded-0 t-views-button"]',
            "Shares": '//button[@class="btn btn-primary rounded-0 t-shares-button"]',
            "Favorites": '//button[@class="btn btn-primary rounded-0 t-favorites-button"]',
            "Live Stream": '//button[@class="btn btn-primary rounded-0 t-livestream-button"]'
        }

        for text, xpath in buttons.items():
            try:
                button = self.driver.find_element(By.XPATH, xpath)
                if not button.get_attribute("disabled"):
                    available_modes.append(text)
            except Exception as e:
                log_message(self.app, f"Error finding button {text}: {e}")

        self.app.mode_menu = ctk.CTkOptionMenu(self.app.mode_frame, variable=self.app.mode_var, values=available_modes)
        self.app.mode_menu.grid(row=1, column=0, padx=20, pady=10)

        self.app.start_button.configure(text="Start", command=self.app.start_bot)

    def get_captcha(self):
        url = "http://zefoy.com"  # Replace with the actual URL of the main page

        try:
            self.driver.get(url)
            # Wait for the page to load
            WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))

            for attempt in range(3):
                try:
                    # Wait for the captcha image to be present
                    captcha_img_tag = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, '//img[@class="img-thumbnail card-img-top border-0"]'))
                    )  # Using an XPath selector

                    if captcha_img_tag:
                        log_message(self.app, "Captcha image found")
                        # Take a screenshot of the captcha image element
                        captcha_img_tag.screenshot('captcha.png')
                        log_message(self.app, "Captcha saved as captcha.png")
                        image = Image.open('captcha.png')
                        captcha_text = self.read_captcha(image)
                        log_message(self.app, f"Captcha text: {captcha_text}")

                        # Find the input field and send the captcha text
                        input_field = self.driver.find_element(By.XPATH, '//input[@class="form-control form-control-lg text-center rounded-0 remove-spaces"]')
                        input_field.send_keys(captcha_text)
                        log_message(self.app, "Captcha text entered")

                        time.sleep(3)  # Wait for 5 seconds before proceeding

                        # Check if the specified element is present
                        if self.driver.find_elements(By.XPATH, '/html/body/div[6]/div/div[2]/div/div/div[1]'):
                            log_message(self.app, "Setup complete. Select mode and start the bot. Make sure you have entered the correct URL.")
                            break
                    else:
                        log_message(self.app, "Captcha image not found on the main page")
                except Exception as e:
                    log_message(self.app, f"Attempt {attempt + 1} failed: {e}")
                    if attempt < 2:
                        time.sleep(3)  # Wait for 3 seconds before retrying
                    else:
                        log_message(self.app, "Max attempts reached. Exiting. Please restart the application.")
                        return  # Exit the function
        except Exception as e:
            log_message(self.app, f"Error during captcha solving: {e}")

    def read_captcha(self, image):
        config = r'--oem 3 --psm 6'
        return pytesseract.image_to_string(image, config=config)

    def parse_wait_time(self, text):
        match = re.search(r'(\d+) minute\(s\) (\d{1,2}) second\(s\)', text)
        if not match:
            match = re.search(r'(\d+) minute\(s\) (\d{1,2}) seconds', text)
        if match:
            minutes = int(match.group(1))
            seconds = int(match.group(2))
            return minutes * 60 + seconds + 2
        else:
            log_message(self.app, f"Failed to parse wait time from text: {text}")
        return 0

    def increment_mode_count(self, mode):
        if mode == "Views":
            self.app.views += 1000
            log_message(self.app, f"Views incremented by 1000")
        elif mode == "Hearts":
            increment = random.randint(11, 15)
            self.app.hearts += increment
            log_message(self.app, f"Hearts incremented by {increment}")
        elif mode == "Shares":
            increment = random.randint(70, 80)
            self.app.shares += increment
            log_message(self.app, f"Shares incremented by {increment}")
        elif mode == "Favorites":
            increment = random.randint(3, 6)
            self.app.favorites += increment
            log_message(self.app, f"Favorites incremented by {increment}")

    def loop(self, vidUrl, mode, amount):
        data = {
            "Followers": {
                "MainButton": '//button[@class="btn btn-primary rounded-0 t-followers-button"]',
                "Input": '/html/body/div[9]/div/form/div/input', 
                "Send": '/html/body/div[9]/div/div/div[1]/div/form/button',
                "Search": '/html/body/div[9]/div/form/div/div/button',
                "TextBeforeSend": '/html/body/div[9]/div/div/span',
                "TextAfterSend": '/html/body/div[9]/div/div/span[1]'
            },
            "Hearts": {
                "MainButton": '//button[@class="btn btn-primary rounded-0 t-hearts-button"]',
                "Input": '/html/body/div[8]/div/form/div/input', 
                "Send": '/html/body/div[8]/div/div/div[1]/div/form/button',
                "Search": '/html/body/div[8]/div/form/div/div/button',
                "TextBeforeSend": '/html/body/div[8]/div/div/span',
                "TextAfterSend": '/html/body/div[8]/div/div/span[1]'
            },
            "Views": {
                "MainButton": '//button[@class="btn btn-primary rounded-0 t-views-button"]',
                "Input": '/html/body/div[10]/div/form/div/input', 
                "Send": '/html/body/div[10]/div/div/div[1]/div/form/button',
                "Search": '/html/body/div[10]/div/form/div/div/button',
                "TextBeforeSend": '/html/body/div[10]/div/div/span',
                "TextAfterSend": '/html/body/div[10]/div/div/span[1]'
            },
            "Shares": {
                "MainButton": '//button[@class="btn btn-primary rounded-0 t-shares-button"]',
                "Input": '/html/body/div[11]/div/form/div/input', 
                "Send": '/html/body/div[11]/div/div/div[1]/div/form/button',
                "Search": '/html/body/div[11]/div/form/div/div/button',
                "TextBeforeSend": '/html/body/div[11]/div/div/span',
                "TextAfterSend": '/html/body/div[11]/div/div/span[1]'
            },
            "Favorites": {
                "MainButton": '//button[@class="btn btn-primary rounded-0 t-favorites-button"]',
                "Input": '/html/body/div[12]/div/form/div/input', 
                "Send": '/html/body/div[12]/div/div/div[1]/div/form/button',
                "Search": '/html/body/div[12]/div/form/div/div/button',
                "TextBeforeSend": '/html/body/div[12]/div/div/span',
                "TextAfterSend": '/html/body/div[12]/div/div/span[1]'
            },
        }

        while self.running:  # Check the flag in the loop condition
            try:
                self.driver.refresh()
                time.sleep(2)
                self.driver.find_element(By.XPATH, data[mode]["MainButton"]).click()
                time.sleep(2)
                self.driver.find_element(By.XPATH, data[mode]["Input"]).send_keys(vidUrl)
                time.sleep(2)
                self.driver.find_element(By.XPATH, data[mode]["Search"]).click()
                time.sleep(6)

                # Check for delay after Search
                wait_text = self.driver.find_element(By.XPATH, data[mode]["TextBeforeSend"]).text
                if wait_text:
                    wait_seconds = self.parse_wait_time(wait_text)
                    if wait_seconds > 0:
                        current_time = time.time() - self.app.start_time
                        future_time = time.strftime('%H:%M:%S', time.gmtime(current_time + wait_seconds))
                        log_message(self.app, f"Wait {wait_seconds} seconds for your next submit (at {future_time} Elapsed Time)")
                        time.sleep(wait_seconds)
                        self.driver.refresh()
                        continue  # Skip the rest of the loop and start over

                self.driver.find_element(By.XPATH, data[mode]["Send"]).click()
                time.sleep(7)
                
                # Extract wait time after Send
                wait_text = self.driver.find_element(By.XPATH, data[mode]["TextAfterSend"]).text
                time.sleep(1)
                wait_seconds = self.parse_wait_time(wait_text)
                current_time = time.time() - self.app.start_time
                future_time = time.strftime('%H:%M:%S', time.gmtime(current_time + wait_seconds))
                log_message(self.app, f"Wait {wait_seconds} seconds for your next submit (at {future_time} Elapsed Time)")

                # Increment counts based on mode
                self.increment_mode_count(mode)

                # Check if the amount limit is reached
                if (mode == "Views" and self.app.views >= amount) or \
                   (mode == "Hearts" and self.app.hearts >= amount) or \
                   (mode == "Followers" and self.app.followers >= amount) or \
                   (mode == "Shares" and self.app.shares >= amount) or \
                   (mode == "Favorites" and self.app.favorites >= amount):
                    log_message(self.app, f"{mode} limit reached: {amount}")
                    self.app.stop_bot()
                    break

                time.sleep(wait_seconds)
            except Exception as e:
                log_message(self.app, f"Error in {mode} loop: {e}")
                self.driver.refresh()
                time.sleep(5)
