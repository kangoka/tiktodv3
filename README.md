<p align="center">
    <img src="https://i.imgur.com/mpXJ5nf.png" alt="Logo" width="300">
</p>

# TIKTOD V3

## Description
TIKTOD V3 is a bot application designed to automate interactions on Zefoy website, such as increasing views, hearts, followers, and shares on a specified video. The bot uses technologies like Selenium for web automation and OCR (Optical Character Recognition) for solving captchas.

## Preview
Here is a screenshot of the TIKTOD V3 application:

<p align="left">
    <img src="https://i.imgur.com/X9PH9Hp.png" alt="TIKTOD V3 Screenshot" width="600">
</p>

## Updates
- Added a graphical user interface using `tkinter` and `customtkinter`.
- Refactored codebase to follow a modular structure for better maintainability and scalability.
- Implemented threading to handle bot operations without freezing the UI.
- Added support for multiple modes: Views, Hearts, Followers, Shares.
- Automatic captcha solving using OCR with `pytesseract`.
- Enhanced logging and status updates in the UI.
- Added dark mode support.
- Added feature to auto-detect available modes on the website.

## Watch the Installation Video
If you are unsure how to install the application, please watch this [installation video](https://youtu.be/50gvfn1zg-w) for a step-by-step guide, or for a demo of the bot.

## Prerequisites

- Google Chrome (version 89 or later) must be installed on your system.
- Python 3.7 or higher must be installed on your system.


## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/kangoka/tiktodv3.git
    ```
2. Navigate to the project directory:
    ```sh
    cd tiktodv3
    ```
3. Install the required packages:
    ```sh
    pip install -r requirements.txt
    ```

## Usage

Before running the application, edit `bot.py` and find the line:
```python
chrome_options.add_extension('C:/Temp/ublock.crx')
```
Change the path to match the location of your `ublock.crx` file.

1. Run the application:
   ```sh
   python app.py
   ```
2. Enter the TikTok video URL in the provided input field.
3. Select the desired mode (Views, Hearts, Followers, Shares) from the sidebar.
4. Click the "Setup" button to initialize the bot.
5. Click the "Start" button to begin the automation process.
6. To stop the application or change the mode, click the "Stop" button.


## Contributing
Contributions are welcome! Please fork the repository and submit a pull request with your changes.

## Disclaimer

This project is intended for educational purposes only. The use of this bot to manipulate TikTok metrics may violate TikTok's terms of service and could result in legal consequences. Use it responsibly, ethically, and at your own risk.

## Acknowledgements

Thanks to Zefoy for providing free services and previous contributors for their valuable input and support.

## Issues

If you encounter any issues while using TIKTOD V3, please open an issue on the [GitHub repository](https://github.com/kangoka/tiktodv3/issues) with detailed information about the issue, including:
   - Steps to reproduce the issue.
   - Any error messages or logs.
   - Your operating system and Python version.