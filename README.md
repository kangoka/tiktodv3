<p align="center">
    <img src="https://i.imgur.com/mpXJ5nf.png" alt="Logo" width="300">
</p>

## Table of Contents
- [Description](#description)
- [Preview](#preview)
- [Features](#features)
- [Watch the Installation Video](#watch-the-installation-video-outdated)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [Disclaimer](#disclaimer)
- [Acknowledgements](#acknowledgements)
- [Issues](#issues)

# TIKTOD V3

## Description
TIKTOD V3 is a bot application designed to automate interactions on Zefoy website, such as increasing views, hearts, followers, and shares on a specified video. The bot uses technologies like Selenium for web automation and OCR (Optical Character Recognition) for solving captchas.

## Preview
Here is a screenshot of the TIKTOD V3 application:

<p align="left">
    <img src="https://i.imgur.com/X9PH9Hp.png" alt="TIKTOD V3 Screenshot" width="600">
</p>

## Features
- User-friendly interface using `customtkinter`.
- Added feature to auto-detect available modes on the website.
- Automatic captcha solving using OCR with `pytesseract`.
- Light mode and dark mode support.
- Detailed stats.

## Watch the Installation Video (outdated)
If you are unsure how to install the application, please watch this [installation video](https://youtu.be/50gvfn1zg-w) for a step-by-step guide, or for a demo of the bot.

## Prerequisites
- Google Chrome (version 89 or later) must be installed on your system. You can download it from [here](https://www.google.com/chrome/).
- Ensure Tesseract OCR is installed on your system. You can download it from [here](https://github.com/tesseract-ocr/tesseract/releases/latest). 
Additionally, make sure to add Tesseract to your system PATH. Follow this [tutorial](https://www.architectryan.com/2018/03/17/add-to-the-path-on-windows-10/) for instructions on how to add it to the PATH on Windows 10.
- Python 3.7 or higher must be installed on your system. You can download it from [here](https://www.python.org/downloads/).

> **Note:** If you plan to use the executable version, you do not need to install Python. Ensure that Python (if you plan to use the source code) and Tesseract OCR are added to your system's PATH.


## Installation

1. Download the latest release zip or executable from the [releases page](https://github.com/kangoka/tiktodv3/releases).
2. If you downloaded the zip file, extract it to a directory of your choice.
3. Navigate to the extracted directory or the directory containing the executable.

## Usage

### Option 1: Using Source Code

1. Install the required packages:
    ```sh
    pip install -r requirements.txt
    ```
2. Run the application:
    ```sh
    python app.py
    ```

### Option 2: Using Executable

1. Run the executable file directly.

2. Enter the TikTok video URL in the provided input field.
3. Click the "Setup" button to initialize the bot.
4. Select the desired mode (Views, Hearts, Followers, Shares) from the sidebar.
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