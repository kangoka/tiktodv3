import queue
import random
import re
import threading
import time
from typing import Any

from .captcha_solver import CaptchaNotReadyError, CaptchaSolver
from .config import (
    CAPTCHA_READY_TIMEOUT_SECONDS,
    CAPTCHA_SAMPLE_INTERVAL_MS,
    CAPTCHA_STABLE_SAMPLES,
    MAX_CONSECUTIVE_FAILURES,
    MAX_CONSECUTIVE_RATE_LIMITS,
    MODE_CONFIGS,
    RATE_LIMIT_MAX_BACKOFF_SECONDS,
    RATE_LIMIT_MIN_BACKOFF_SECONDS,
    SERVICE_URL,
    SUPPORTED_MODES,
    WORKER_CLOSE_TIMEOUT_SECONDS,
)

WAIT_TIME_RE = re.compile(
    r"(\d+)\s*minute(?:\(s\)|s?)\s*(\d{1,2})\s*second(?:\(s\)|s?)",
    re.IGNORECASE,
)
BUSY_RE = re.compile(r"server is too busy.*?(\d+)\s*seconds?", re.IGNORECASE)
PENDING_RE = re.compile(r"please wait.*sending", re.IGNORECASE)
PENDING_COUNT_RE = re.compile(r"please wait[^\d]*(\d[\d,]*)\b.*sending", re.IGNORECASE)
RATE_LIMIT_RE = re.compile(
    r"too many requests|please slow down|rate limit(?:ed)?", re.IGNORECASE
)


class Bot:
    def __init__(self, log_callback, progress_callback=None, captcha_solver=None):
        self.log_callback = log_callback
        self.progress_callback = progress_callback
        self.captcha_solver = captcha_solver or CaptchaSolver()
        self._cancel_event = threading.Event()
        self._closed = False
        self._close_lock = threading.Lock()
        self._counts = {mode: 0 for mode in SUPPORTED_MODES}
        self._elapsed_base = 0.0
        self._run_started_at = None

        # Browser state (owned by the worker thread only)
        self._browser: Any = None
        self._context: Any = None
        self.page: Any = None

        # Dedicated worker thread for all Playwright calls.
        # Playwright's sync API requires every call to be made from the
        # thread that created the playwright instance.
        self._cmd_queue: queue.Queue[Any] = queue.Queue()
        self._worker_thread = None

    def _log(self, message):
        """Emit a message without touching Tk from the worker thread."""
        if self.log_callback:
            self.log_callback(message)

    def _notify_progress(self):
        if self.progress_callback:
            self.progress_callback(dict(self._counts))

    # ------------------------------------------------------------------
    # Worker thread plumbing
    # ------------------------------------------------------------------
    def _ensure_worker(self):
        if self._closed:
            raise RuntimeError("Bot worker is already closed")
        if self._worker_thread is None or not self._worker_thread.is_alive():
            self._worker_thread = threading.Thread(
                target=self._worker_loop, daemon=True
            )
            self._worker_thread.start()

    def _worker_loop(self):
        while True:
            cmd = self._cmd_queue.get()
            if cmd is None:
                break
            func, args, kwargs, callback = cmd
            try:
                result = func(*args, **kwargs)
                if callback:
                    callback((result, None))
            except Exception as exc:  # noqa: BLE001
                if callback:
                    callback((None, exc))
                else:
                    self._log(f"Worker error: {exc}")

    def _submit(self, func, *args, wait=True, timeout=None, **kwargs):
        self._ensure_worker()
        if not wait:
            self._cmd_queue.put((func, args, kwargs, None))
            return None

        done = threading.Event()
        box = {}

        def _cb(payload):
            box["result"] = payload
            done.set()

        self._cmd_queue.put((func, args, kwargs, _cb))
        if not done.wait(timeout):
            raise TimeoutError(f"Worker command timed out: {func.__name__}")
        result, err = box["result"]
        if err:
            raise err
        return result

    # ------------------------------------------------------------------
    # Public API (called from tkinter threads)
    # ------------------------------------------------------------------
    def setup_bot(self):
        """Launch CloakBrowser and solve the Zefoy captcha."""
        try:
            return self._submit(self._do_setup)
        except Exception:
            try:
                self._submit(self._do_close, timeout=10)
            except Exception:  # noqa: BLE001
                pass
            raise

    def prepare_run(self, elapsed_seconds=0.0):
        """Clear cancellation before one new automation run starts."""
        self._cancel_event.clear()
        self._elapsed_base = max(0.0, elapsed_seconds)
        self._run_started_at = time.monotonic()

    def request_stop(self):
        """Request cooperative cancellation from any thread."""
        self._cancel_event.set()

    def loop(self, vid_url, mode, amount):
        """Run the main interaction loop on the worker thread."""
        return self._submit(self._do_loop, vid_url, mode, amount)

    def close(self):
        """Tear down the browser and worker. Safe to call multiple times."""
        with self._close_lock:
            if self._closed:
                return
            self.request_stop()
            if self._worker_thread is not None and self._worker_thread.is_alive():
                try:
                    self._submit(self._do_close, timeout=WORKER_CLOSE_TIMEOUT_SECONDS)
                except Exception as exc:  # noqa: BLE001
                    self._log(f"Browser shutdown warning: {exc}")
                self._cmd_queue.put(None)
                self._worker_thread.join(timeout=2)
            self._closed = True

    # ------------------------------------------------------------------
    # Worker-side implementations
    # ------------------------------------------------------------------
    def _do_setup(self):
        self._log("Setting up the bot...")

        if self._browser is not None or self._context is not None:
            self._do_close()

        self._log("Checking local dependencies...")
        self.captcha_solver.ensure_available()
        self._launch_browser()

        if not self._get_captcha():
            self._do_close()
            raise RuntimeError(
                "Setup could not verify the captcha. Please try Setup again."
            )

        available_modes, disabled_modes = self._discover_modes()
        if not available_modes:
            self._do_close()
            raise RuntimeError(
                "Setup succeeded, but no supported modes are currently available. "
                "Please try again later."
            )

        return {
            "available_modes": tuple(available_modes),
            "disabled_modes": frozenset(disabled_modes),
        }

    def _launch_browser(self):
        """Launch one browser/context/page on the Playwright worker thread."""
        try:
            from cloakbrowser import launch
        except ImportError as exc:
            raise RuntimeError(
                "CloakBrowser is unavailable. Reinstall the project dependencies "
                "and retry Setup."
            ) from exc

        self._log("Launching CloakBrowser (stealth Chromium)...")
        self._browser = launch(
            headless=False,
            humanize=True,  # human-like mouse, keyboard, scroll timing
        )
        self._context = self._browser.new_context()
        self.page = self._context.new_page()

        # Block the funding-choices overlay that used to be blocked via CDP.
        try:
            self.page.route(
                "**/fundingchoicesmessages.google.com/**",
                lambda route: route.abort(),
            )
        except Exception as exc:  # noqa: BLE001
            self._log(f"Route block warning: {exc}")

    def _discover_modes(self):
        """Return supported modes that are available and disabled."""
        available_modes = []
        disabled_modes = set()
        for text, mode_config in MODE_CONFIGS.items():
            try:
                first = self._wait_for_visible_locator(
                    mode_config.main_button_selectors,
                    timeout=2000,
                    required=False,
                )
                if first is None:
                    continue

                has_disabled_attr = first.get_attribute("disabled") is not None
                class_attr = first.get_attribute("class") or ""
                has_disabled_class = "disabled" in class_attr.split()

                if has_disabled_attr or has_disabled_class:
                    disabled_modes.add(text)
                    self._log(f"Mode '{text}' is disabled on Zefoy")
                else:
                    available_modes.append(text)
            except Exception as exc:  # noqa: BLE001
                self._log(f"Error finding button {text}: {exc}")
        return available_modes, disabled_modes

    def _get_captcha(self):
        try:
            self.page.goto(SERVICE_URL, wait_until="domcontentloaded", timeout=30000)
            self.page.wait_for_selector("body", timeout=20000)

            for attempt in range(3):
                try:
                    if self._solve_captcha_attempt():
                        return True
                except Exception as exc:  # noqa: BLE001
                    self._log(f"Attempt {attempt + 1} failed: {exc}")
                    if attempt < 2:
                        self.page.wait_for_timeout(1000)
                    else:
                        self._log(
                            "Setup did not complete after three attempts. Please try again.",
                        )
                        return False
        except Exception as exc:  # noqa: BLE001
            self._log(f"Error during captcha solving: {exc}")
            return False

        return False

    def _solve_captcha_attempt(self):
        captcha_img = self._wait_for_visible_locator(
            ("#captcha-img", 'xpath=//*[@id="captcha-img"]'),
            timeout=10000,
        )
        self._log("Captcha image found")
        captcha_text = self._wait_for_ready_captcha(captcha_img)
        self._log("Captcha OCR completed")

        input_locator = self._wait_for_visible_locator(
            (
                "input.remove-spaces",
                'xpath=//input[contains(@class, "remove-spaces")]',
            ),
            timeout=10000,
        )
        input_locator.fill(captcha_text)
        input_locator.press("Enter")
        self._log("Captcha text entered")

        success = self._wait_for_visible_locator(
            tuple(config.main_button_selectors[0] for config in MODE_CONFIGS.values()),
            timeout=5000,
            required=False,
        )
        if success is None:
            return False

        self._log(
            "Setup complete. Select mode and start the bot. "
            "Make sure you have entered the correct URL."
        )
        return True

    def _wait_for_ready_captcha(self, captcha_img):
        """Wait for a stable, non-placeholder CAPTCHA before running OCR."""
        deadline = time.monotonic() + CAPTCHA_READY_TIMEOUT_SECONDS
        last_fingerprint = None
        stable_samples = 0
        rejected_fingerprint = None

        while time.monotonic() < deadline:
            src = (captcha_img.get_attribute("src") or "").lower()
            if any(word in src for word in ("loading", "spinner", "placeholder")):
                last_fingerprint = None
                stable_samples = 0
                self.page.wait_for_timeout(CAPTCHA_SAMPLE_INTERVAL_MS)
                continue

            image_bytes = captcha_img.screenshot()
            fingerprint = self.captcha_solver.fingerprint(image_bytes)
            if fingerprint == last_fingerprint:
                stable_samples += 1
            else:
                last_fingerprint = fingerprint
                stable_samples = 1
                rejected_fingerprint = None

            if (
                stable_samples >= CAPTCHA_STABLE_SAMPLES
                and fingerprint != rejected_fingerprint
            ):
                try:
                    return self.captcha_solver.solve(image_bytes)
                except CaptchaNotReadyError:
                    rejected_fingerprint = fingerprint
                    self._log("Captcha is still loading; waiting for the real image...")

            self.page.wait_for_timeout(CAPTCHA_SAMPLE_INTERVAL_MS)

        raise RuntimeError(
            "Captcha image did not finish loading within "
            f"{CAPTCHA_READY_TIMEOUT_SECONDS} seconds"
        )

    def parse_wait_time(self, text):
        match = WAIT_TIME_RE.search(text)
        if match:
            minutes = int(match.group(1))
            seconds = int(match.group(2))
            return minutes * 60 + seconds + 2

        # Zefoy occasionally returns: "The server is too busy. Please try
        # again in X seconds."
        busy = BUSY_RE.search(text)
        if busy:
            return int(busy.group(1)) + 2

        self._log(f"Failed to parse wait time from text: {text}")
        return 0

    def increment_mode_count(self, mode, observed_increment=None):
        if mode not in MODE_CONFIGS:
            raise ValueError(f"Unsupported mode: {mode}")

        mode_config = MODE_CONFIGS[mode]
        if observed_increment is None:
            minimum, maximum = mode_config.default_increment_range
            increment = random.randint(minimum, maximum)
            source = "estimated"
        else:
            increment = observed_increment
            source = "confirmed"

        self._counts[mode] += increment
        self._log(f"{mode} incremented by {increment} ({source})")
        self._notify_progress()
        return increment

    def _elapsed_seconds(self):
        if self._run_started_at is None:
            return self._elapsed_base
        return self._elapsed_base + (time.monotonic() - self._run_started_at)

    def _wait_for_visible_locator(self, selectors, timeout=10000, required=True):
        per_selector_timeout = max(250, timeout // max(1, len(selectors)))
        for selector in selectors:
            locator = self.page.locator(selector).first
            try:
                locator.wait_for(state="visible", timeout=per_selector_timeout)
                return locator
            except Exception:  # selector fallback is intentional
                continue

        if required:
            raise RuntimeError(
                "The service page changed and a required control could not be found"
            )
        return None

    def _first_visible_locator(self, selectors):
        for selector in selectors:
            try:
                locator = self.page.locator(selector).first
                if locator.count() > 0 and locator.is_visible():
                    return locator
            except Exception:  # selector fallback is intentional
                continue
        return None

    def _read_first_text(self, selectors):
        locator = self._first_visible_locator(selectors)
        if locator is None:
            return ""
        try:
            return locator.inner_text().strip()
        except Exception:
            return ""

    def _do_loop(self, vid_url, mode, amount):
        if mode not in MODE_CONFIGS:
            raise ValueError(f"Unsupported mode: {mode}")

        mode_config = MODE_CONFIGS[mode]
        consecutive_failures = 0
        consecutive_rate_limits = 0
        while not self._cancel_event.is_set():
            try:
                action, wait_text, send_button = self._prepare_submission(
                    mode_config, vid_url
                )
                if action == "cooldown":
                    consecutive_failures = 0
                    consecutive_rate_limits = 0
                    self._sleep_interruptible(self._parse_and_log_wait(wait_text, mode))
                    continue
                if action == "rate_limited":
                    consecutive_failures = 0
                    consecutive_rate_limits += 1
                    if not self._handle_rate_limit(mode, consecutive_rate_limits):
                        if self._cancel_event.is_set():
                            return "stopped"
                        return "rate_limited"
                    continue

                status, wait_seconds, observed_increment = self._submit_and_wait(
                    send_button, mode_config, mode
                )

                if status == "busy":
                    consecutive_failures = 0
                    consecutive_rate_limits = 0
                    self._log(
                        f"{mode} was not confirmed because the server is busy. "
                        "Waiting before retrying.",
                    )
                    self._sleep_interruptible(wait_seconds)
                    continue
                if status == "rate_limited":
                    consecutive_failures = 0
                    consecutive_rate_limits += 1
                    if not self._handle_rate_limit(mode, consecutive_rate_limits):
                        if self._cancel_event.is_set():
                            return "stopped"
                        return "rate_limited"
                    continue

                self.increment_mode_count(mode, observed_increment)

                if self._counts[mode] >= amount:
                    self._log(f"{mode} limit reached: {amount}")
                    return "limit_reached"

                consecutive_failures = 0
                consecutive_rate_limits = 0
                self._sleep_interruptible(wait_seconds)
            except Exception as exc:  # noqa: BLE001
                if self._cancel_event.is_set():
                    break

                consecutive_failures += 1
                if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                    raise RuntimeError(
                        f"{mode} stopped after {consecutive_failures} consecutive "
                        f"failures. Last error: {exc}"
                    ) from exc

                backoff_seconds = min(2**consecutive_failures, 10)
                self._log(
                    f"{mode} attempt failed ({consecutive_failures}/"
                    f"{MAX_CONSECUTIVE_FAILURES}): {exc}. Retrying in "
                    f"{backoff_seconds} seconds."
                )
                self._sleep_interruptible(backoff_seconds)

        return "stopped"

    def _handle_rate_limit(self, mode, occurrence):
        if occurrence >= MAX_CONSECUTIVE_RATE_LIMITS:
            self._log(
                f"{mode} stopped because the service rate limit remained active "
                f"across {occurrence} checks. Wait at least 15-30 minutes before "
                "starting again; repeated requests can extend the restriction."
            )
            return False

        wait_seconds = random.randint(
            RATE_LIMIT_MIN_BACKOFF_SECONDS,
            RATE_LIMIT_MAX_BACKOFF_SECONDS,
        )
        self._log(
            "The service reported 'Too many requests.' Nothing was counted. "
            f"Pausing for {wait_seconds} seconds before a cautious recheck "
            f"({occurrence}/{MAX_CONSECUTIVE_RATE_LIMITS})."
        )
        self._sleep_interruptible(wait_seconds)
        return not self._cancel_event.is_set()

    def _prepare_submission(self, mode_config, vid_url):
        self.page.reload(wait_until="domcontentloaded", timeout=30000)
        self._wait_for_visible_locator(mode_config.main_button_selectors).click()
        self._wait_for_visible_locator(mode_config.input_selectors).fill(vid_url)
        self._wait_for_visible_locator(mode_config.search_button_selectors).click()
        return self._wait_for_send_or_cooldown(mode_config)

    def _submit_and_wait(self, send_button, mode_config, mode):
        send_button.click()
        status, wait_text, observed_increment = self._wait_for_final_status(
            mode_config.after_status_selectors, mode
        )
        if status == "timeout":
            raise RuntimeError(
                f"Timed out waiting for a final {mode} submission status; "
                "the result was not counted."
            )
        if status == "rate_limited":
            return status, 0, None
        return status, self._parse_and_log_wait(wait_text, mode), observed_increment

    def _parse_and_log_wait(self, wait_text, mode):
        wait_seconds = self.parse_wait_time(wait_text)
        if wait_seconds <= 0:
            raise RuntimeError(
                f"Could not determine the next safe {mode} submission time; "
                "the result was not counted."
            )
        future_time = time.strftime(
            "%H:%M:%S",
            time.gmtime(self._elapsed_seconds() + wait_seconds),
        )
        self._log(
            f"Wait {wait_seconds} seconds for your next submit "
            f"(at {future_time} Elapsed Time)"
        )
        return wait_seconds

    def _wait_for_send_or_cooldown(self, mode_config, timeout_seconds=15):
        end = time.time() + timeout_seconds
        while not self._cancel_event.is_set() and time.time() < end:
            wait_text = self._read_first_text(mode_config.before_status_selectors)
            if wait_text and RATE_LIMIT_RE.search(wait_text):
                return "rate_limited", wait_text, None
            if wait_text and (
                WAIT_TIME_RE.search(wait_text) or BUSY_RE.search(wait_text)
            ):
                return "cooldown", wait_text, None

            send_button = self._first_visible_locator(mode_config.send_button_selectors)
            if send_button is not None:
                try:
                    if send_button.is_enabled():
                        return "send", "", send_button
                except Exception:
                    pass

            self.page.wait_for_timeout(250)

        raise RuntimeError("Timed out waiting for the Send action")

    def _sleep_interruptible(self, seconds):
        """Sleep in small slices so stop_bot() takes effect quickly."""
        end = time.time() + max(0, seconds)
        while not self._cancel_event.is_set() and time.time() < end:
            time.sleep(min(0.5, end - time.time()))

    def _wait_for_final_status(self, selectors, mode, timeout_seconds=180):
        """Poll Zefoy's status line until the 'Please wait, X are sending'
        in-flight message clears and the real wait-time text appears.

        Returns ``(state, text, observed_increment)``. State is ``sent``,
        ``busy``, ``rate_limited``, or ``timeout``.
        """
        end = time.time() + timeout_seconds
        last_logged = None
        observed_increment = None
        text = ""

        while not self._cancel_event.is_set() and time.time() < end:
            text = self._read_first_text(selectors)

            # Done: we see the "X minute(s) Y second(s)" cooldown message
            # or the "server is too busy ... N seconds" back-off message.
            if text and WAIT_TIME_RE.search(text):
                return "sent", text, observed_increment
            if text and BUSY_RE.search(text):
                return "busy", text, None
            if text and RATE_LIMIT_RE.search(text):
                return "rate_limited", text, None

            # Still in flight: keep polling, log once so the user knows why.
            if text and PENDING_RE.search(text):
                count_match = PENDING_COUNT_RE.search(text)
                if count_match:
                    observed_increment = int(count_match.group(1).replace(",", ""))
                if last_logged != text:
                    self._log(
                        f"{mode} still sending, waiting for Zefoy to finish...",
                    )
                    last_logged = text
                self.page.wait_for_timeout(500)
                continue

            # Some other transient text — give it a moment.
            self.page.wait_for_timeout(500)

        return "timeout", text, observed_increment

    def _do_close(self):
        try:
            if self._context is not None:
                self._context.close()
        except Exception:  # noqa: BLE001
            pass
        try:
            if self._browser is not None:
                self._browser.close()
        except Exception:  # noqa: BLE001
            pass
        self._context = None
        self._browser = None
        self.page = None
