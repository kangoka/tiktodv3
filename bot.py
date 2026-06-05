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
        # NOTE: Headless mode disabled for debugging - re-enable after fixing
        # chrome_options.add_argument("--headless")  # Enable headless mode
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-webgl")
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_argument("--log-level=3")  # Suppress most logs
        chrome_options.add_argument("--disable-logging")  # Disable logging
        chrome_options.add_argument("--disable-notifications")  # Disable notification prompts
        
        # Block notification permission prompts
        prefs = {
            "profile.default_content_settings.popups": 0,
            "profile.default_content_setting_values.notifications": 2,  # 2 = BLOCK
            "profile.default_content_settings.state.notifications": 2
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        # Block permission dialogs
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=chrome_options)

        # Override window.alert to prevent alerts from blocking
        self.driver.execute_cdp_cmd("Page.enable", {})
        self.driver.execute_cdp_cmd("Page.setInterceptFileChooserDialog", {"enabled": False})
        
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
            "Followers": '//button[contains(@class, "t-followers-button")]',
            "Hearts": '//button[contains(@class, "t-hearts-button")]',
            "Views": '//button[contains(@class, "t-views-button")]',
            "Shares": '//button[contains(@class, "t-shares-button")]',
            "Favorites": '//button[contains(@class, "t-favorites-button")]',
            "Live Stream": '//button[contains(@class, "t-livestream-button")]'
        }

        # Wait for buttons to load
        time.sleep(3)
        for text, xpath in buttons.items():
            try:
                # Try with explicit wait
                try:
                    button = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, xpath))
                    )
                    if not button.get_attribute("disabled"):
                        available_modes.append(text)
                except:
                    # Fallback to direct find
                    button = self.driver.find_element(By.XPATH, xpath)
                    if not button.get_attribute("disabled"):
                        available_modes.append(text)
            except Exception as e:
                log_message(self.app, f"Error finding button {text}: {e}")

        self.app.mode_menu = ctk.CTkOptionMenu(self.app.mode_frame, variable=self.app.mode_var, values=available_modes)
        self.app.mode_menu.grid(row=1, column=0, padx=20, pady=10)

        self.app.start_button.configure(text="Start", command=self.app.start_bot)

    def get_captcha(self):
        url = "http://zefoy.com"

        try:
            # Override alert/confirm on page
            self.driver.execute_script("""
                window.originalAlert = window.alert;
                window.originalConfirm = window.confirm;
                window.alert = function(msg) { 
                    console.log('Alert blocked:', msg);
                    return true;
                };
                window.confirm = function(msg) { 
                    console.log('Confirm blocked:', msg);
                    return true;
                };
            """)
            
            self.driver.get(url)
            log_message(self.app, "Page loaded, waiting for body element...")
            
            # Wait for the page to load
            WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
            log_message(self.app, "Page body element found")

            # Multiple attempts to dismiss any alerts that might appear
            dismissal_attempts = 0
            for attempt in range(10):
                try:
                    alert = WebDriverWait(self.driver, 1).until(EC.alert_is_present())
                    log_message(self.app, f"Alert {dismissal_attempts + 1} detected: {alert.text}")
                    alert.dismiss()
                    dismissal_attempts += 1
                    time.sleep(0.5)
                except:
                    if dismissal_attempts > 0:
                        log_message(self.app, f"All {dismissal_attempts} alerts dismissed")
                    break

            for attempt in range(3):
                try:
                    log_message(self.app, f"Attempt {attempt + 1}: Waiting for captcha image...")
                    time.sleep(2)  # Extra wait before looking for captcha
                    
                    # Try flexible XPath first
                    try:
                        captcha_img_tag = WebDriverWait(self.driver, 8).until(
                            EC.presence_of_element_located((By.XPATH, '//img[contains(@class, "img-thumbnail")]'))
                        )
                        log_message(self.app, "Captcha image found with flexible selector")
                    except:
                        # Try other variations
                        log_message(self.app, "Trying to find any img element on page...")
                        try:
                            captcha_img_tag = WebDriverWait(self.driver, 3).until(
                                EC.presence_of_element_located((By.TAG_NAME, 'img'))
                            )
                            log_message(self.app, f"Found img element: {captcha_img_tag}")
                        except:
                            # Save HTML for debugging
                            html = self.driver.page_source
                            with open('page_source.html', 'w', encoding='utf-8') as f:
                                f.write(html)
                            log_message(self.app, "Page HTML saved to page_source.html for debugging")
                            raise Exception("No img element found on page")

                    if captcha_img_tag:
                        log_message(self.app, "Captcha image found, taking screenshot...")
                        captcha_img_tag.screenshot('captcha.png')
                        log_message(self.app, "Captcha saved as captcha.png")
                        image = Image.open('captcha.png')
                        captcha_text = self.read_captcha(image)
                        log_message(self.app, f"Captcha text: {captcha_text}")

                        # Find the input field and send the captcha text
                        input_field = self.driver.find_element(By.XPATH, '//input[@class="form-control form-control-lg text-center rounded-0 remove-spaces"]')
                        input_field.send_keys(captcha_text)
                        log_message(self.app, "Captcha text entered")

                        time.sleep(3)

                        # Check if the specified element is present
                        if self.driver.find_elements(By.XPATH, '/html/body/div[6]/div/div[2]/div/div/div[1]'):
                            log_message(self.app, "Setup complete. Select mode and start the bot. Make sure you have entered the correct URL.")
                            break
                    else:
                        log_message(self.app, "Captcha image not found on the main page")
                except Exception as e:
                    log_message(self.app, f"Attempt {attempt + 1} failed: {str(e)}")
                    # Take screenshot for debugging
                    try:
                        self.driver.save_screenshot(f'debug_attempt_{attempt + 1}.png')
                        log_message(self.app, f"Debug screenshot saved as debug_attempt_{attempt + 1}.png")
                    except:
                        pass
                    
                    if attempt < 2:
                        log_message(self.app, f"Retrying in 3 seconds...")
                        time.sleep(3)
                    else:
                        log_message(self.app, "Max attempts reached. Please check if the URL is correct and the website is accessible.")
        except Exception as e:
            log_message(self.app, f"Error during captcha solving: {e}")

    def read_captcha(self, image):
        config = r'--oem 3 --psm 6'
        return pytesseract.image_to_string(image, config=config)

    def parse_wait_time(self, text):
        # Check for rate limit message first
        if "too many requests" in text.lower():
            log_message(self.app, f"Rate limited by server, waiting 60 seconds...")
            return 60
        
        match = re.search(r'(\d+) minute\(s\) (\d{1,2}) second\(s\)', text)
        if not match:
            match = re.search(r'(\d+) minute\(s\) (\d{1,2}) seconds', text)
        if match:
            minutes = int(match.group(1))
            seconds = int(match.group(2))
            return minutes * 60 + seconds + 2
        else:
            log_message(self.app, f"Failed to parse wait time from text: {text}")
            # Default to 30 seconds if parsing fails
            return 30
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
                "MainButton": '//button[contains(@class, "t-followers-button")]',
                "Input": '/html/body/div[9]/div/form/div/input', 
                "Send": '/html/body/div[9]/div/div/div[1]/div/form/button',
                "Search": '/html/body/div[9]/div/form/div/div/button',
                "TextBeforeSend": '/html/body/div[9]/div/div/span',
                "TextAfterSend": '/html/body/div[9]/div/div/span[1]'
            },
            "Hearts": {
                "MainButton": '//button[contains(@class, "t-hearts-button")]',
                "Input": '/html/body/div[8]/div/form/div/input', 
                "Send": '/html/body/div[8]/div/div/div[1]/div/form/button',
                "Search": '/html/body/div[8]/div/form/div/div/button',
                "TextBeforeSend": '/html/body/div[8]/div/div/span',
                "TextAfterSend": '/html/body/div[8]/div/div/span[1]'
            },
            "Views": {
                "MainButton": '//button[contains(@class, "t-views-button")]',
                "Input": '/html/body/div[10]/div/form/div/input', 
                "Send": '/html/body/div[10]/div/div/div[1]/div/form/button',
                "Search": '/html/body/div[10]/div/form/div/div/button',
                "TextBeforeSend": '/html/body/div[10]/div/div/span',
                "TextAfterSend": '/html/body/div[10]/div/div/span[1]'
            },
            "Shares": {
                "MainButton": '//button[contains(@class, "t-shares-button")]',
                "Input": '/html/body/div[11]/div/form/div/input', 
                "Send": '/html/body/div[11]/div/div/div[1]/div/form/button',
                "Search": '/html/body/div[11]/div/form/div/div/button',
                "TextBeforeSend": '/html/body/div[11]/div/div/span',
                "TextAfterSend": '/html/body/div[11]/div/div/span[1]'
            },
            "Favorites": {
                "MainButton": '//button[contains(@class, "t-favorites-button")]',
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
                
                # Handle any alerts that may appear
                for _ in range(5):
                    try:
                        alert = WebDriverWait(self.driver, 1).until(EC.alert_is_present())
                        alert.dismiss()
                        time.sleep(0.5)
                    except:
                        break  # No alert
                
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
                
                # Extract wait time after Send and check for success
                wait_text = self.driver.find_element(By.XPATH, data[mode]["TextAfterSend"]).text
                log_message(self.app, f"Server response: {wait_text}")
                
                # Check if submission was successful or failed
                if "error" in wait_text.lower() or "failed" in wait_text.lower():
                    log_message(self.app, f"Submission failed! Server says: {wait_text}")
                    wait_seconds = 30  # Default wait on error
                elif "too many requests" in wait_text.lower():
                    log_message(self.app, f"Rate limited, waiting 60 seconds...")
                    wait_seconds = 60
                else:
                    time.sleep(1)
                    wait_seconds = self.parse_wait_time(wait_text)
                
                current_time = time.time() - self.app.start_time
                future_time = time.strftime('%H:%M:%S', time.gmtime(current_time + wait_seconds))
                log_message(self.app, f"Wait {wait_seconds} seconds for your next submit (at {future_time} Elapsed Time)")

                # Only increment if submission seems successful (not an error message)
                if "error" not in wait_text.lower() and "failed" not in wait_text.lower():
                    self.increment_mode_count(mode)
                else:
                    log_message(self.app, f"Skipping increment - submission appears to have failed")

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
