"""Fast deterministic project checks that do not contact external services."""

from unittest.mock import patch

from tiktodv3.bot import RATE_LIMIT_RE, Bot
from tiktodv3.captcha_solver import CaptchaNotReadyError, CaptchaSolver
from tiktodv3.config import (
    MAX_CONSECUTIVE_RATE_LIMITS,
    MODE_CONFIGS,
    RATE_LIMIT_MAX_BACKOFF_SECONDS,
    RATE_LIMIT_MIN_BACKOFF_SECONDS,
    SUPPORTED_MODES,
)
from tiktodv3.gui import normalize_tiktok_url


def check_urls():
    assert normalize_tiktok_url("vm.tiktok.com/abc") == "https://vm.tiktok.com/abc"
    assert normalize_tiktok_url("https://www.tiktok.com/@owner/video/123").endswith(
        "/video/123"
    )

    invalid_urls = (
        "",
        "https://tiktok.com/",
        "https://example.com/video/1",
        "ftp://tiktok.com/video/1",
        "https://user:pass@tiktok.com/video/1",
    )
    for value in invalid_urls:
        try:
            normalize_tiktok_url(value)
        except ValueError:
            continue
        raise AssertionError(f"Accepted invalid URL: {value}")


def check_modes_and_status_parsing():
    assert tuple(MODE_CONFIGS) == SUPPORTED_MODES
    assert "Live Stream" not in SUPPORTED_MODES

    progress: list[dict[str, int]] = []
    bot = Bot(log_callback=lambda message: None, progress_callback=progress.append)
    assert bot.parse_wait_time("1 minute 5 seconds") == 67
    assert bot.parse_wait_time("2 minute(s) 07 second(s)") == 129
    assert bot.parse_wait_time("Server is too busy; retry in 9 seconds") == 11

    bot.increment_mode_count("Followers", 7)
    assert progress[-1]["Followers"] == 7


def check_retry_limit():
    bot = Bot(log_callback=lambda message: None)
    bot.page = object()
    bot.prepare_run()
    attempts: list[int] = []

    def fail(*args):
        attempts.append(1)
        raise RuntimeError("page changed")

    bot._prepare_submission = fail  # type: ignore[method-assign]
    bot._sleep_interruptible = lambda seconds: None  # type: ignore[method-assign]
    try:
        bot._do_loop("https://tiktok.com/@owner/video/1", "Views", 1)
    except RuntimeError as exc:
        assert "3 consecutive failures" in str(exc)
    else:
        raise AssertionError("Retry circuit breaker did not open")
    assert len(attempts) == 3


def check_captcha_text_validation():
    assert CaptchaSolver.normalize_text(" A-b 12\n") == "Ab12"
    with patch(
        "tiktodv3.captcha_solver.pytesseract.image_to_string",
        return_value="Loading",
    ):
        with patch("tiktodv3.captcha_solver.Image.open") as image_open:
            image_open.return_value.__enter__.return_value = object()
            try:
                CaptchaSolver.solve(b"placeholder")
            except CaptchaNotReadyError:
                pass
            else:
                raise AssertionError("Captcha loading text was accepted")

    class FakeCaptchaSolver:
        solve_calls = 0

        @staticmethod
        def fingerprint(image_bytes):
            return image_bytes.decode()

        def solve(self, image_bytes):
            self.solve_calls += 1
            if image_bytes == b"loading":
                raise CaptchaNotReadyError("still loading")
            return "Ab12"

    class FakeCaptchaLocator:
        def __init__(self):
            self.samples = iter((b"loading", b"loading", b"ready", b"ready"))
            self.last_sample = b"ready"

        @staticmethod
        def get_attribute(name):
            return "/captcha/image"

        def screenshot(self):
            self.last_sample = next(self.samples, self.last_sample)
            return self.last_sample

    solver = FakeCaptchaSolver()
    bot = Bot(log_callback=lambda message: None, captcha_solver=solver)
    bot.page = type("FakePage", (), {"wait_for_timeout": lambda self, ms: None})()
    assert bot._wait_for_ready_captcha(FakeCaptchaLocator()) == "Ab12"
    assert solver.solve_calls == 2


def check_rate_limit_handling():
    assert RATE_LIMIT_RE.search("Too many requests. Please slow down.")

    logs: list[str] = []
    bot = Bot(log_callback=logs.append)
    bot._sleep_interruptible = lambda seconds: None  # type: ignore[method-assign]
    with patch(
        "tiktodv3.bot.random.randint",
        return_value=RATE_LIMIT_MIN_BACKOFF_SECONDS,
    ) as randint:
        assert bot._handle_rate_limit("Views", 1)
        randint.assert_called_once_with(
            RATE_LIMIT_MIN_BACKOFF_SECONDS, RATE_LIMIT_MAX_BACKOFF_SECONDS
        )
    assert "Nothing was counted" in logs[-1]
    assert not bot._handle_rate_limit("Views", MAX_CONSECUTIVE_RATE_LIMITS)

    checks: list[int] = []

    def rate_limited(*args):
        checks.append(1)
        return "rate_limited", "Too many requests. Please slow down.", None

    bot._prepare_submission = rate_limited  # type: ignore[method-assign]
    assert (
        bot._do_loop("https://tiktok.com/@owner/video/1", "Views", 1) == "rate_limited"
    )
    assert len(checks) == MAX_CONSECUTIVE_RATE_LIMITS


def main():
    check_urls()
    check_modes_and_status_parsing()
    check_retry_limit()
    check_captcha_text_validation()
    check_rate_limit_handling()
    print("Project verification passed")


if __name__ == "__main__":
    main()
