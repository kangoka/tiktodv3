"""Application metadata and automation policy."""

from dataclasses import dataclass

APP_NAME = "TIKTOD V3"
APP_VERSION = "2.0.0"
REPOSITORY_URL = "https://github.com/kangoka/tiktodv3"
SERVICE_URL = "https://zefoy.com"

MAX_CONSECUTIVE_FAILURES = 3
MAX_CONSECUTIVE_RATE_LIMITS = 3
RATE_LIMIT_MIN_BACKOFF_SECONDS = 90
RATE_LIMIT_MAX_BACKOFF_SECONDS = 180
CAPTCHA_READY_TIMEOUT_SECONDS = 20
CAPTCHA_STABLE_SAMPLES = 2
CAPTCHA_SAMPLE_INTERVAL_MS = 400
MAX_URL_LENGTH = 2048
WORKER_CLOSE_TIMEOUT_SECONDS = 15


@dataclass(frozen=True)
class ModeConfig:
    name: str
    counter_name: str
    default_increment_range: tuple[int, int]
    main_button_selectors: tuple[str, ...]
    input_selectors: tuple[str, ...]
    search_button_selectors: tuple[str, ...]
    send_button_selectors: tuple[str, ...]
    before_status_selectors: tuple[str, ...]
    after_status_selectors: tuple[str, ...]


def _mode(name, slug, panel_index, increment_range):
    return ModeConfig(
        name=name,
        counter_name=name.lower(),
        default_increment_range=increment_range,
        main_button_selectors=(
            f"button.t-{slug}-button",
            f'xpath=//button[contains(@class, "t-{slug}-button")]',
        ),
        input_selectors=(
            "input.form-control:visible",
            f"xpath=/html/body/div[{panel_index}]/div/form/div/input",
        ),
        search_button_selectors=(
            'button:visible:has-text("Search")',
            f"xpath=/html/body/div[{panel_index}]/div/form/div/div/button",
        ),
        send_button_selectors=(
            'button:visible:has-text("Send")',
            f"xpath=/html/body/div[{panel_index}]/div/div/div[1]/div/form/button",
        ),
        before_status_selectors=(
            "text=/minute\\(s\\)|server is too busy|too many requests|please slow down/i",
            f"xpath=/html/body/div[{panel_index}]/div/div/span",
        ),
        after_status_selectors=(
            "text=/please wait.*sending|minute\\(s\\)|server is too busy|too many requests|please slow down/i",
            f"xpath=/html/body/div[{panel_index}]/div/div/span[1]",
        ),
    )


MODE_CONFIGS = {
    mode.name: mode
    for mode in (
        _mode("Followers", "followers", 9, (1, 1)),
        _mode("Hearts", "hearts", 8, (11, 15)),
        _mode("Views", "views", 10, (1000, 1000)),
        _mode("Shares", "shares", 11, (70, 80)),
        _mode("Favorites", "favorites", 12, (3, 6)),
    )
}

SUPPORTED_MODES = tuple(MODE_CONFIGS)
