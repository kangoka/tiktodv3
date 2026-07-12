# Third-Party Notices

TIKTOD V3 depends on third-party software. The Apache-2.0 license for TIKTOD V3
does not replace or modify the licenses of these components.

| Component | Pinned version | License | Copyright/source |
|---|---:|---|---|
| CustomTkinter | 5.2.2 | MIT | Copyright © 2023 Tom Schimansky; [project site](https://customtkinter.tomschimansky.com) |
| CloakBrowser | 0.3.28 | MIT | Copyright © 2026 CloakHQ; [source](https://github.com/CloakHQ/CloakBrowser) |
| Playwright for Python | 1.59.0 | Apache-2.0 | Copyright Microsoft Corporation; [source](https://github.com/microsoft/playwright-python) |
| Pillow | 12.2.0 | MIT-CMU | Copyright © 1995-2011 Fredrik Lundh and contributors, © 1997-2011 Secret Labs AB, and © 2010 Jeffrey A. Clark and contributors; [source](https://github.com/python-pillow/Pillow) |
| pytesseract | 0.3.13 | Apache-2.0 | Copyright Samuel Hoffstaetter and contributors; [source](https://github.com/madmaze/pytesseract) |

The authoritative license files are included in each pinned package distribution.
Playwright's browser driver also carries its own `NOTICE` and
`ThirdPartyNotices.txt`. Release packaging must retain all applicable dependency,
Python runtime, browser-driver, and PyInstaller bootloader notices.

Tesseract OCR and CloakBrowser's patched Chromium are external runtime components
and are not intentionally embedded in the one-file executable. Their independent
licenses still apply when installed or downloaded.
