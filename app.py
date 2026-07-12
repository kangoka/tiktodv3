"""Backward-compatible launcher for ``python app.py``."""

from tiktodv3.gui import App, AppState, main, normalize_tiktok_url

__all__ = ["App", "AppState", "main", "normalize_tiktok_url"]


if __name__ == "__main__":
    main()
