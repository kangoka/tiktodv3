import queue
import threading
import time
import tkinter as tk
from collections.abc import Callable
from enum import Enum, auto
from typing import Any
from urllib.parse import urlparse

import customtkinter as ctk
from PIL import Image

from .bot import Bot
from .config import (
    APP_NAME,
    APP_VERSION,
    MAX_URL_LENGTH,
    REPOSITORY_URL,
    SUPPORTED_MODES,
)
from .settings import AppSettings
from .theme import (
    COLOR,
    CONTROL_HEIGHT,
    DEFAULT_WINDOW_SIZE,
    MIN_WINDOW_SIZE,
    SIDEBAR_WIDTH,
    SPACE,
)
from .utils import log_message, resource_path


def normalize_tiktok_url(value):
    value = value.strip()
    if not value:
        raise ValueError("Please enter a TikTok video URL")
    if len(value) > MAX_URL_LENGTH or any(character.isspace() for character in value):
        raise ValueError("TikTok video URL is too long or contains spaces")

    candidate = value if "://" in value else f"https://{value}"
    parsed = urlparse(candidate)
    hostname = (parsed.hostname or "").lower().rstrip(".")

    if parsed.scheme not in {"http", "https"}:
        raise ValueError("TikTok video URL must use http or https")
    if parsed.username or parsed.password:
        raise ValueError("TikTok video URL must not contain credentials")
    if hostname != "tiktok.com" and not hostname.endswith(".tiktok.com"):
        raise ValueError("Please enter a URL from tiktok.com")
    if not parsed.path or parsed.path == "/":
        raise ValueError("Please enter a TikTok video URL, not the TikTok homepage")

    return candidate


class AppState(Enum):
    IDLE = auto()
    SETTING_UP = auto()
    READY = auto()
    RUNNING = auto()
    STOPPING = auto()
    ERROR = auto()
    CLOSING = auto()


class App(ctk.CTk):
    def __init__(self):
        self.settings = AppSettings.load()
        ctk.set_appearance_mode(self.settings.theme)
        super().__init__()

        self.app_state = AppState.IDLE
        self._ui_queue: queue.Queue[tuple[Callable[..., Any], tuple[Any, ...]]] = (
            queue.Queue()
        )
        self._ui_poll_id = None
        self._stats_after_id = None
        self._setup_thread = None
        self._run_thread = None

        self.title(APP_NAME)
        self.geometry(f"{DEFAULT_WINDOW_SIZE[0]}x{DEFAULT_WINDOW_SIZE[1]}")
        self.minsize(*MIN_WINDOW_SIZE)
        self.configure(fg_color=COLOR["window"])
        try:
            self.iconbitmap(resource_path("assets/logo.ico"))
        except tk.TclError:
            self._window_icon = tk.PhotoImage(
                file=resource_path("assets/dark-logo.png")
            )
            self.iconphoto(True, self._window_icon)

        # Configure grid layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Create sidebar frame with widgets
        self.sidebar_frame = ctk.CTkFrame(
            self,
            width=SIDEBAR_WIDTH,
            corner_radius=0,
            fg_color=COLOR["sidebar"],
        )
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_propagate(False)
        self.sidebar_frame.grid_rowconfigure(9, weight=1)

        self.heading_font = ctk.CTkFont(family="Bahnschrift", size=18, weight="bold")
        self.label_font = ctk.CTkFont(family="Bahnschrift", size=13, weight="bold")
        self.body_font = ctk.CTkFont(family="Segoe UI", size=13)
        self.meta_font = ctk.CTkFont(family="Segoe UI", size=11)
        self.log_font = ctk.CTkFont(family="Cascadia Mono", size=12)
        self.data_font = ctk.CTkFont(family="Bahnschrift", size=16, weight="bold")

        self.logo_image_dark = ctk.CTkImage(
            light_image=Image.open(resource_path("assets/dark-logo.png")),
            size=(88, 88),
        )
        self.logo_image_light = ctk.CTkImage(
            light_image=Image.open(resource_path("assets/light-logo.png")),
            size=(88, 88),
        )
        self.logo_image_label = ctk.CTkLabel(
            self.sidebar_frame,
            image=(
                self.logo_image_dark
                if self.settings.theme == "dark"
                else self.logo_image_light
            ),
            text="",
        )
        self.logo_image_label.grid(
            row=0, column=0, padx=SPACE["lg"], pady=(SPACE["lg"], SPACE["md"])
        )

        self.link_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="TikTok video URL",
            font=self.label_font,
            text_color=COLOR["text"],
            anchor="w",
        )
        self.link_label.grid(
            row=1,
            column=0,
            padx=SPACE["lg"],
            pady=(SPACE["sm"], SPACE["xs"]),
            sticky="w",
        )
        self.link_entry = ctk.CTkEntry(
            self.sidebar_frame,
            width=SIDEBAR_WIDTH - (SPACE["lg"] * 2),
            height=CONTROL_HEIGHT,
            font=self.body_font,
            placeholder_text="tiktok.com/@user/video/...",
            fg_color=COLOR["surface"],
            text_color=COLOR["text"],
            border_color=COLOR["border"],
        )
        self.link_entry.grid(row=2, column=0, padx=SPACE["lg"], pady=SPACE["xs"])

        self.amount_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="Target amount",
            font=self.label_font,
            text_color=COLOR["text"],
            anchor="w",
        )
        self.amount_label.grid(
            row=3,
            column=0,
            padx=SPACE["lg"],
            pady=(SPACE["md"], SPACE["xs"]),
            sticky="w",
        )
        self.amount_entry = ctk.CTkEntry(
            self.sidebar_frame,
            width=SIDEBAR_WIDTH - (SPACE["lg"] * 2),
            height=CONTROL_HEIGHT,
            font=self.body_font,
            placeholder_text="Positive whole number",
            fg_color=COLOR["surface"],
            text_color=COLOR["text"],
            border_color=COLOR["border"],
        )
        self.amount_entry.grid(row=4, column=0, padx=SPACE["lg"], pady=SPACE["xs"])

        self.start_button = ctk.CTkButton(
            self.sidebar_frame,
            text="Setup",
            command=self.start_setup,
            font=self.label_font,
            height=CONTROL_HEIGHT,
            fg_color=COLOR["accent"],
            hover_color=COLOR["accent_hover"],
            text_color=COLOR["accent_text"],
            border_width=1,
            border_color=COLOR["accent"],
        )
        self.start_button.grid(
            row=6, column=0, padx=SPACE["lg"], pady=SPACE["lg"], sticky="ew"
        )

        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color=COLOR["window"])
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.grid_rowconfigure(2, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        self.status_frame = ctk.CTkFrame(
            self.main_frame, fg_color=COLOR["surface_alt"], corner_radius=8
        )
        self.status_frame.grid(
            row=0,
            column=0,
            padx=SPACE["lg"],
            pady=(SPACE["lg"], SPACE["sm"]),
            sticky="ew",
        )
        self.status_frame.grid_columnconfigure(1, weight=1)
        self.status_caption = ctk.CTkLabel(
            self.status_frame,
            text="SYSTEM STATUS",
            font=self.meta_font,
            text_color=COLOR["muted"],
        )
        self.status_caption.grid(
            row=0, column=0, rowspan=2, padx=SPACE["md"], pady=SPACE["md"]
        )
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="NOT SET UP",
            font=self.heading_font,
            text_color=COLOR["text"],
            anchor="w",
        )
        self.status_label.grid(
            row=0, column=1, padx=(0, SPACE["md"]), pady=(SPACE["sm"], 0), sticky="w"
        )
        self.status_detail = ctk.CTkLabel(
            self.status_frame,
            text="Review the notice, then set up the browser.",
            font=self.meta_font,
            text_color=COLOR["muted"],
            anchor="w",
        )
        self.status_detail.grid(
            row=1, column=1, padx=(0, SPACE["md"]), pady=(0, SPACE["sm"]), sticky="w"
        )

        self.disclosure_var = tk.BooleanVar(value=self.settings.disclosure_accepted)
        self.disclosure_frame = ctk.CTkFrame(
            self.main_frame,
            fg_color=COLOR["warning_surface"],
            corner_radius=8,
        )
        self.disclosure_frame.grid(
            row=1,
            column=0,
            padx=SPACE["lg"],
            pady=SPACE["sm"],
            sticky="ew",
        )
        self.disclosure_frame.grid_columnconfigure(0, weight=1)
        self.disclosure_text = ctk.CTkLabel(
            self.disclosure_frame,
            text=(
                "This tool sends the entered TikTok URL to Zefoy and automates "
                "third-party interactions. This can violate platform rules. Use it "
                "only where you are authorized and accept the account and privacy risks."
            ),
            font=self.body_font,
            text_color=COLOR["warning_text"],
            justify="left",
            anchor="w",
            wraplength=560,
        )
        self.disclosure_text.grid(
            row=0,
            column=0,
            padx=SPACE["md"],
            pady=(SPACE["md"], SPACE["xs"]),
            sticky="ew",
        )
        self.disclosure_checkbox = ctk.CTkCheckBox(
            self.disclosure_frame,
            text="I understand the risks and am authorized to continue",
            variable=self.disclosure_var,
            command=self.on_disclosure_changed,
            font=self.label_font,
            text_color=COLOR["warning_text"],
            fg_color=COLOR["accent"],
            hover_color=COLOR["accent_hover"],
            border_color=COLOR["warning_text"],
            height=CONTROL_HEIGHT,
        )
        self.disclosure_checkbox.grid(
            row=1, column=0, padx=SPACE["md"], pady=(0, SPACE["sm"]), sticky="w"
        )

        self.tab_view = ctk.CTkTabview(
            self.main_frame,
            fg_color=COLOR["surface"],
            segmented_button_fg_color=COLOR["surface_alt"],
            segmented_button_selected_color=COLOR["accent"],
            segmented_button_selected_hover_color=COLOR["accent_hover"],
            segmented_button_unselected_color=COLOR["accent_hover"],
            segmented_button_unselected_hover_color=COLOR["accent"],
            text_color=COLOR["accent_text"],
        )
        self.tab_view.grid(
            row=2,
            column=0,
            padx=SPACE["lg"],
            pady=SPACE["sm"],
            sticky="nsew",
        )
        self.tab_view._segmented_button.configure(  # noqa: SLF001
            font=self.body_font,
        )

        self.log_tab = self.tab_view.add("Log")
        self.log_tab.grid_rowconfigure(1, weight=1)
        self.log_tab.grid_columnconfigure(0, weight=1)
        self.log_toolbar = ctk.CTkFrame(
            self.log_tab, fg_color="transparent", corner_radius=0
        )
        self.log_toolbar.grid(
            row=0, column=0, padx=SPACE["md"], pady=SPACE["sm"], sticky="ew"
        )
        self.log_toolbar.grid_columnconfigure(0, weight=1)
        self.log_hint = ctk.CTkLabel(
            self.log_toolbar,
            text="Browser and automation events",
            font=self.meta_font,
            text_color=COLOR["muted"],
        )
        self.log_hint.grid(row=0, column=0, sticky="w")
        self.copy_log_button = ctk.CTkButton(
            self.log_toolbar,
            text="Copy log",
            command=self.copy_log,
            width=92,
            height=CONTROL_HEIGHT,
            font=self.body_font,
            fg_color="transparent",
            hover_color=COLOR["surface_alt"],
            text_color=COLOR["text"],
            border_width=1,
            border_color=COLOR["border"],
        )
        self.copy_log_button.grid(row=0, column=1, padx=SPACE["xs"])
        self.clear_log_button = ctk.CTkButton(
            self.log_toolbar,
            text="Clear",
            command=self.clear_log,
            width=76,
            height=CONTROL_HEIGHT,
            font=self.body_font,
            fg_color="transparent",
            hover_color=COLOR["surface_alt"],
            text_color=COLOR["text"],
            border_width=1,
            border_color=COLOR["border"],
        )
        self.clear_log_button.grid(row=0, column=2, padx=(SPACE["xs"], 0))
        self.log_text = ctk.CTkTextbox(
            self.log_tab,
            font=self.log_font,
            fg_color=COLOR["log"],
            text_color=COLOR["text"],
            border_width=1,
            border_color=COLOR["border"],
        )
        self.log_text.grid(
            row=1,
            column=0,
            padx=SPACE["md"],
            pady=(0, SPACE["md"]),
            sticky="nsew",
        )
        self.log_text.configure(state="disabled")

        self.stats_tab = self.tab_view.add("Stats")
        for tab_button in self.tab_view._segmented_button._buttons_dict.values():  # noqa: SLF001
            tab_button.configure(height=CONTROL_HEIGHT)
        self.stats_tab.grid_rowconfigure(0, weight=1)
        self.stats_tab.grid_columnconfigure(0, weight=1)

        self.stats_frame = ctk.CTkFrame(
            self.stats_tab,
            fg_color="transparent",
            corner_radius=0,
        )
        self.stats_frame.grid(
            row=0, column=0, padx=SPACE["md"], pady=SPACE["md"], sticky="nsew"
        )
        self.stats_frame.grid_columnconfigure(0, weight=1)
        self.stats_frame.grid_columnconfigure(1, weight=1)

        self.stats_header = ctk.CTkFrame(
            self.stats_frame, fg_color="transparent", corner_radius=0
        )
        self.stats_header.grid(
            row=0, column=0, columnspan=2, padx=SPACE["sm"], sticky="ew"
        )
        self.stats_header.grid_columnconfigure(0, weight=1)
        self.stats_title = ctk.CTkLabel(
            self.stats_header,
            text="Session overview",
            font=self.heading_font,
            text_color=COLOR["text"],
            anchor="w",
        )
        self.stats_title.grid(row=0, column=0, sticky="w")
        self.stats_scope = ctk.CTkLabel(
            self.stats_header,
            text="Confirmed since the app was opened",
            font=self.meta_font,
            text_color=COLOR["muted"],
            anchor="e",
        )
        self.stats_scope.grid(row=0, column=1, sticky="e")

        self.stats_progress_frame = ctk.CTkFrame(
            self.stats_frame,
            fg_color=COLOR["surface_alt"],
            corner_radius=8,
        )
        self.stats_progress_frame.grid(
            row=1,
            column=0,
            columnspan=2,
            padx=SPACE["sm"],
            pady=(SPACE["xs"], SPACE["md"]),
            sticky="ew",
        )
        self.stats_progress_frame.grid_columnconfigure(0, weight=1)
        self.stats_progress_title = ctk.CTkLabel(
            self.stats_progress_frame,
            text="No target selected",
            font=self.label_font,
            text_color=COLOR["text"],
            anchor="w",
        )
        self.stats_progress_title.grid(
            row=0,
            column=0,
            padx=SPACE["md"],
            pady=(SPACE["md"], 0),
            sticky="w",
        )
        self.stats_progress_value = ctk.CTkLabel(
            self.stats_progress_frame,
            text="0 / —",
            font=self.data_font,
            text_color=COLOR["text"],
            anchor="e",
        )
        self.stats_progress_value.grid(
            row=0,
            column=1,
            padx=SPACE["md"],
            pady=(SPACE["md"], 0),
            sticky="e",
        )
        self.stats_progress = ctk.CTkProgressBar(
            self.stats_progress_frame,
            height=8,
            corner_radius=4,
            fg_color=COLOR["border"],
            progress_color=COLOR["success"],
        )
        self.stats_progress.grid(
            row=1,
            column=0,
            columnspan=2,
            padx=SPACE["md"],
            pady=(SPACE["sm"], SPACE["md"]),
            sticky="ew",
        )
        self.stats_progress.set(0)

        self.stats_metrics_frame = ctk.CTkFrame(
            self.stats_frame, fg_color="transparent", corner_radius=0
        )
        for column in range(6):
            self.stats_metrics_frame.grid_columnconfigure(column, weight=1)
        self.stats_metrics_heading = ctk.CTkLabel(
            self.stats_metrics_frame,
            text="CONFIRMED THIS APP SESSION",
            font=self.meta_font,
            text_color=COLOR["muted"],
            anchor="w",
        )
        self.stats_metrics_heading.grid(
            row=0, column=0, columnspan=2, pady=(0, SPACE["xs"]), sticky="w"
        )

        self.stats_count_labels = {}
        metric_names = (
            ("Views", "views"),
            ("Hearts", "hearts"),
            ("Followers", "followers"),
            ("Shares", "shares"),
            ("Favorites", "favorites"),
        )
        for column, (label_text, key) in enumerate(metric_names):
            label = ctk.CTkLabel(
                self.stats_metrics_frame,
                text=label_text,
                font=self.body_font,
                text_color=COLOR["text"],
                anchor="center",
            )
            label.grid(row=1, column=column, sticky="ew")
            value = ctk.CTkLabel(
                self.stats_metrics_frame,
                text="0",
                font=self.data_font,
                text_color=COLOR["text"],
                anchor="center",
            )
            value.grid(row=2, column=column, pady=(0, SPACE["xs"]), sticky="ew")
            self.stats_count_labels[key] = value

        self.stats_total_label = ctk.CTkLabel(
            self.stats_metrics_frame,
            text="Total",
            font=self.label_font,
            text_color=COLOR["text"],
            anchor="center",
        )
        self.stats_total_label.grid(row=1, column=5, sticky="ew")
        self.stats_total_value = ctk.CTkLabel(
            self.stats_metrics_frame,
            text="0",
            font=self.data_font,
            text_color=COLOR["text"],
            anchor="center",
        )
        self.stats_total_value.grid(row=2, column=5, pady=(0, SPACE["xs"]), sticky="ew")

        self.stats_metrics_note = ctk.CTkLabel(
            self.stats_metrics_frame,
            text="Confirmed responses only; failures and limits are excluded.",
            font=self.meta_font,
            text_color=COLOR["muted"],
            anchor="e",
        )
        self.stats_metrics_note.grid(
            row=0,
            column=2,
            columnspan=4,
            pady=(0, SPACE["xs"]),
            sticky="e",
        )

        self.stats_progress_meta = ctk.CTkLabel(
            self.stats_progress_frame,
            text="Not set up · Elapsed 00:00:00",
            font=self.meta_font,
            text_color=COLOR["muted"],
            anchor="w",
        )
        self.stats_progress_meta.grid(
            row=2,
            column=0,
            columnspan=2,
            padx=SPACE["md"],
            pady=(0, SPACE["md"]),
            sticky="w",
        )

        self._stats_compact = None
        self._layout_stats_sections(DEFAULT_WINDOW_SIZE[0])

        self.footer_frame = ctk.CTkFrame(
            self.main_frame, fg_color="transparent", corner_radius=0
        )
        self.footer_frame.grid(
            row=3, column=0, padx=SPACE["lg"], pady=(0, SPACE["sm"]), sticky="ew"
        )
        self.footer_frame.grid_columnconfigure(0, weight=1)
        self.shortcut_label = ctk.CTkLabel(
            self.footer_frame,
            text="Alt+S action  ·  Alt+M mode  ·  Alt+T theme  ·  Ctrl+Tab panels  ·  Esc stop",
            font=self.meta_font,
            text_color=COLOR["muted"],
        )
        self.shortcut_label.grid(row=0, column=0, sticky="w")
        self.version_label = ctk.CTkLabel(
            self.footer_frame,
            text=f"v{APP_VERSION}",
            font=self.meta_font,
            text_color=COLOR["muted"],
        )
        self.version_label.grid(row=0, column=1, padx=SPACE["sm"])
        self.github_link = ctk.CTkButton(
            self.footer_frame,
            text="GitHub",
            command=self.open_github,
            width=76,
            height=CONTROL_HEIGHT,
            font=self.body_font,
            fg_color="transparent",
            hover_color=COLOR["surface_alt"],
            text_color=COLOR["text"],
            border_width=1,
            border_color=COLOR["border"],
        )
        self.github_link.grid(row=0, column=2, sticky="e")

        self.mode_var = tk.StringVar(value="")
        self.mode_frame: Any = None
        self.mode_menu: Any = None
        self.disabled_modes: set[str] = set()
        self.bot = Bot(self.post_log, self.post_progress)
        self.elapsed_time = 0.0
        self.views = 0  # Initialize views
        self.hearts = 0  # Initialize hearts
        self.followers = 0  # Initialize followers
        self.shares = 0  # Initialize shares
        self.favorites = 0  # Initialize favorites
        self.stats_mode = None
        self.stats_target = 0
        self.update_stats_label(schedule_next=False)

        self.theme_switch_var = tk.StringVar(value=self.settings.theme)
        self.theme_switch = ctk.CTkSwitch(
            self.sidebar_frame,
            text="Dark theme",
            variable=self.theme_switch_var,
            onvalue="dark",
            offvalue="light",
            command=self.switch_theme,
            font=self.body_font,
            text_color=COLOR["text"],
            progress_color=COLOR["accent"],
            button_color=COLOR["accent_text"],
            button_hover_color=COLOR["focus"],
            border_color=COLOR["border"],
            height=CONTROL_HEIGHT,
        )
        self.theme_switch.grid(
            row=10,
            column=0,
            padx=SPACE["lg"],
            pady=(SPACE["sm"], SPACE["lg"]),
            sticky="sw",
        )

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.bind("<Configure>", self._on_resize, add="+")
        self.bind_all("<Alt-s>", self._activate_primary, add="+")
        self.bind_all("<Alt-t>", self._toggle_theme, add="+")
        self.bind_all("<Alt-m>", self._cycle_mode, add="+")
        self.bind_all("<Control-Tab>", self._cycle_tab, add="+")
        self.bind_all("<Control-l>", self._focus_url, add="+")
        self.bind_all("<Control-g>", lambda event: self.open_github(), add="+")
        self.bind_all("<Escape>", lambda event: self.stop_bot(), add="+")

        self._enable_keyboard_control(self.start_button, self._activate_primary)
        self._enable_keyboard_control(self.copy_log_button, self.copy_log)
        self._enable_keyboard_control(self.clear_log_button, self.clear_log)
        self._enable_keyboard_control(self.github_link, self.open_github)
        self._enable_keyboard_control(
            self.theme_switch, self.theme_switch.toggle, focus_border=False
        )
        self._enable_keyboard_control(
            self.disclosure_checkbox,
            self.disclosure_checkbox.toggle,
            focus_border=False,
        )

        if not self.settings.disclosure_accepted:
            self.start_button.configure(
                text="Accept notice to set up", state="disabled"
            )
        self._append_log(
            "Ready for setup. Review the authorization and privacy notice above."
        )
        self._ui_poll_id = self.after(50, self._process_ui_queue)
        self.after(120, self._center_window)

    def on_close(self):
        if self.app_state is AppState.CLOSING:
            return

        self._set_app_state(AppState.CLOSING)
        self.bot.request_stop()

        for after_id in (self._ui_poll_id, self._stats_after_id):
            if after_id is not None:
                try:
                    self.after_cancel(after_id)
                except Exception:
                    pass

        # Browser cleanup is bounded inside Bot.close(). Keep this thread
        # non-daemon so child browser processes are not abandoned on exit.
        threading.Thread(target=self.bot.close, daemon=False).start()
        self.destroy()

    def _post_ui(self, callback, *args):
        if self.app_state is not AppState.CLOSING:
            self._ui_queue.put((callback, args))

    def _process_ui_queue(self):
        if self.app_state is AppState.CLOSING:
            return

        for _ in range(100):
            try:
                callback, args = self._ui_queue.get_nowait()
            except queue.Empty:
                break
            try:
                callback(*args)
            except Exception as exc:
                self._append_log(f"UI update failed: {exc}")

        self._ui_poll_id = self.after(50, self._process_ui_queue)

    def _append_log(self, message):
        log_message(self, message)

    def post_log(self, message):
        """Thread-safe log entry point used by the automation worker."""
        self._post_ui(self._append_log, message)

    def post_progress(self, counts):
        """Thread-safe counter update entry point used by the worker."""
        self._post_ui(self._apply_progress, counts)

    def _apply_progress(self, counts):
        for mode, count in counts.items():
            setattr(self, mode.lower(), count)
        if self.app_state in {AppState.RUNNING, AppState.STOPPING}:
            self.update_stats_label(schedule_next=False)

    def _set_app_state(self, state, detail=None):
        self.app_state = state
        if not hasattr(self, "status_label"):
            return

        labels = {
            AppState.IDLE: (
                "NOT SET UP",
                "Review the notice, then set up the browser.",
            ),
            AppState.SETTING_UP: (
                "SETTING UP",
                "Checking dependencies, launching the browser, and verifying access.",
            ),
            AppState.READY: ("READY", "Choose a mode and start automation."),
            AppState.RUNNING: ("RUNNING", "Automation is active. Press Esc to stop."),
            AppState.STOPPING: (
                "STOPPING",
                "Waiting for the active browser step to finish.",
            ),
            AppState.ERROR: ("NEEDS ATTENTION", "Review the log, then retry Setup."),
            AppState.CLOSING: ("CLOSING", "Closing browser resources safely."),
        }
        label, default_detail = labels[state]
        self.status_label.configure(text=label)
        self.status_detail.configure(text=detail or default_detail)
        if hasattr(self, "stats_progress_meta"):
            self.update_stats_label(schedule_next=False)

    def _enable_keyboard_control(self, widget, command, focus_border=True):
        canvas = getattr(widget, "_canvas", None)
        if canvas is None:
            return

        canvas.configure(takefocus=True, highlightthickness=0)

        def invoke(event=None):
            command()
            return "break"

        def focus_in(event=None):
            color = COLOR["focus"][0 if self.settings.theme == "light" else 1]
            canvas.configure(
                highlightthickness=2,
                highlightcolor=color,
                highlightbackground=color,
            )
            if focus_border:
                try:
                    widget.configure(border_width=2, border_color=COLOR["focus"])
                except ValueError:
                    pass

        def focus_out(event=None):
            canvas.configure(highlightthickness=0)
            if focus_border:
                try:
                    widget.configure(border_width=1, border_color=COLOR["border"])
                except ValueError:
                    pass

        canvas.bind("<Return>", invoke, add="+")
        canvas.bind("<space>", invoke, add="+")
        canvas.bind("<FocusIn>", focus_in, add="+")
        canvas.bind("<FocusOut>", focus_out, add="+")

    def _activate_primary(self, event=None):
        if self.app_state in {AppState.IDLE, AppState.ERROR}:
            self.start_setup()
        elif self.app_state is AppState.READY:
            self.start_bot()
        elif self.app_state is AppState.RUNNING:
            self.stop_bot()
        return "break"

    def _toggle_theme(self, event=None):
        self.theme_switch.toggle()
        return "break"

    def _cycle_mode(self, event=None):
        available_modes = getattr(self, "available_modes", ())
        if self.app_state is not AppState.READY or not available_modes:
            return "break"
        current_index = available_modes.index(self.mode_var.get())
        self.mode_var.set(available_modes[(current_index + 1) % len(available_modes)])
        return "break"

    def _cycle_tab(self, event=None):
        current = self.tab_view.get()
        self.tab_view.set("Stats" if current == "Log" else "Log")
        return "break"

    def _focus_url(self, event=None):
        self.link_entry.focus_set()
        return "break"

    def _on_resize(self, event):
        if event.widget is not self:
            return
        logical_width = event.width / max(1.0, self._get_window_scaling())
        content_width = max(320, min(540, logical_width - SIDEBAR_WIDTH - 120))
        self.disclosure_text.configure(wraplength=content_width)
        self._layout_stats_sections(logical_width)
        if logical_width < 840:
            self.shortcut_label.configure(
                text="Alt+S action · Alt+M mode · Ctrl+Tab panels · Esc stop"
            )
        else:
            self.shortcut_label.configure(
                text="Alt+S action  ·  Alt+M mode  ·  Alt+T theme  ·  Ctrl+Tab panels  ·  Esc stop"
            )

    def _layout_stats_sections(self, logical_width):
        if not hasattr(self, "stats_metrics_frame"):
            return

        available_width = logical_width - SIDEBAR_WIDTH - (SPACE["lg"] * 2)
        compact = available_width < 560
        if compact == self._stats_compact:
            return

        self.stats_metrics_frame.grid_forget()
        self.stats_metrics_frame.grid(
            row=2,
            column=0,
            columnspan=2,
            padx=SPACE["sm"],
            pady=(0, SPACE["md"]),
            sticky="ew",
        )
        self.stats_metrics_note.configure(
            text=(
                "Failures and limits are excluded."
                if compact
                else "Confirmed responses only; failures and limits are excluded."
            )
        )
        self._stats_compact = compact

    def _center_window(self):
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        safe_height = max(1, self.winfo_screenheight() - 80)
        x = max(0, (screen_width - self.winfo_width()) // 2)
        y = max(20, (safe_height - self.winfo_height()) // 2)
        self.geometry(f"+{x}+{y}")

    def on_disclosure_changed(self):
        accepted = bool(self.disclosure_var.get())
        self.settings.disclosure_accepted = accepted
        self.settings.save()

        if accepted:
            if self.app_state is AppState.IDLE:
                self.start_button.configure(text="Setup", state="normal")
            elif self.app_state is AppState.ERROR:
                self.start_button.configure(text="Retry Setup", state="normal")
            elif self.app_state is AppState.READY:
                self.start_button.configure(text="Start", state="normal")
        elif self.app_state in {AppState.IDLE, AppState.ERROR, AppState.READY}:
            self.start_button.configure(
                text="Accept notice to continue", state="disabled"
            )

    def copy_log(self):
        text = self.log_text.get("1.0", "end-1c")
        self.clipboard_clear()
        self.clipboard_append(text)
        self._append_log("Log copied to the clipboard")

    def clear_log(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")
        self._append_log("Log cleared")

    def open_github(self):
        import webbrowser

        webbrowser.open(REPOSITORY_URL)

    def switch_theme(self):
        theme = self.theme_switch_var.get()
        ctk.set_appearance_mode(theme)
        self.settings.theme = theme
        self.settings.save()
        self.logo_image_label.configure(
            image=self.logo_image_dark if theme == "dark" else self.logo_image_light
        )

    def start_setup(self):
        if not self.settings.disclosure_accepted:
            self._append_log("Accept the authorization and privacy notice before Setup")
            return
        if self.app_state not in {AppState.IDLE, AppState.ERROR}:
            return

        self._set_app_state(AppState.SETTING_UP)
        self.disclosure_checkbox.configure(state="disabled")
        self.start_button.configure(
            text="Setting up...", state="disabled", command=self.start_setup
        )
        self._append_log("Starting browser setup...")
        self._setup_thread = threading.Thread(target=self.setup_bot, daemon=True)
        self._setup_thread.start()

    def setup_bot(self):
        try:
            result = self.bot.setup_bot()
        except Exception as exc:
            self._post_ui(self._on_setup_failed, str(exc))
        else:
            self._post_ui(self._on_setup_succeeded, result)

    def _on_setup_succeeded(self, result):
        available_modes = result["available_modes"]
        self.available_modes = tuple(available_modes)
        self.disabled_modes = set(result["disabled_modes"])

        if self.mode_frame is not None and self.mode_frame.winfo_exists():
            self.mode_frame.destroy()

        self.mode_frame = ctk.CTkFrame(
            self.sidebar_frame, corner_radius=0, fg_color="transparent"
        )
        self.mode_frame.grid(row=5, column=0, padx=20, pady=10, sticky="nsew")

        self.mode_label = ctk.CTkLabel(
            self.mode_frame,
            text="Mode",
            font=self.label_font,
            text_color=COLOR["text"],
        )
        self.mode_label.grid(row=0, column=0, padx=20, pady=(8, 4))
        self.mode_var.set(available_modes[0])
        self.mode_menu = ctk.CTkOptionMenu(
            self.mode_frame,
            variable=self.mode_var,
            values=list(available_modes),
            height=CONTROL_HEIGHT,
            font=self.body_font,
            fg_color=COLOR["accent"],
            button_color=COLOR["accent_hover"],
            button_hover_color=COLOR["focus"],
            text_color=COLOR["accent_text"],
        )
        self.mode_menu.grid(row=1, column=0, padx=20, pady=(4, 8))

        self._enable_keyboard_control(self.mode_menu, self._cycle_mode)
        self._set_app_state(AppState.READY)
        self.disclosure_checkbox.configure(state="normal")
        self.start_button.configure(
            text="Start", state="normal", command=self.start_bot
        )

    def _on_setup_failed(self, message):
        self._set_app_state(AppState.ERROR, message)
        self.disclosure_checkbox.configure(state="normal")
        self._append_log(f"Setup failed: {message}")
        self.start_button.configure(
            text="Retry Setup", state="normal", command=self.start_setup
        )

    def start_bot(self):
        if not self.settings.disclosure_accepted:
            self._append_log(
                "Accept the authorization and privacy notice before starting"
            )
            return
        if self.app_state is not AppState.READY:
            if self.app_state not in {AppState.RUNNING, AppState.STOPPING}:
                self._append_log("Complete Setup before starting the bot")
            return

        auto = self.mode_var.get()

        disabled_modes: set[str] = self.disabled_modes
        if auto.endswith(" (disabled)") or auto in disabled_modes:
            clean = auto.replace(" (disabled)", "")
            self._append_log(
                f"{clean} is currently disabled on Zefoy. Pick another mode."
            )
            return

        try:
            vid_url = normalize_tiktok_url(self.link_entry.get())
        except ValueError as exc:
            self._append_log(str(exc))
            return

        try:
            amount = int(self.amount_entry.get().strip())
        except ValueError:
            self._append_log("Amount must be a whole number")
            return

        if amount <= 0:
            self._append_log("Amount must be greater than zero")
            return

        if auto in SUPPORTED_MODES:
            self.start_time = time.time() - self.elapsed_time
            self.stats_mode = auto
            self.stats_target = amount
            self.log_text.configure(state="normal")
            self.log_text.delete("1.0", tk.END)
            self.log_text.configure(state="disabled")
            self._append_log(APP_NAME)
            self._append_log("Log:")

            self._set_app_state(
                AppState.RUNNING, f"{auto} automation is active. Press Esc to stop."
            )
            self.bot.prepare_run(self.elapsed_time)
            self.link_entry.configure(state="disabled")
            self.amount_entry.configure(state="disabled")
            self.mode_menu.configure(state="disabled")
            self.disclosure_checkbox.configure(state="disabled")

            self.start_button.configure(text="Stop", command=self.stop_bot)
            self.update_stats_label()
            self._run_thread = threading.Thread(
                target=self._run_bot,
                args=(vid_url, auto, amount),
                daemon=True,
            )
            self._run_thread.start()
        else:
            valid_modes = ", ".join(SUPPORTED_MODES)
            self._append_log(f"{auto} is not a valid option. Please pick {valid_modes}")

    def _run_bot(self, vid_url, mode, amount):
        try:
            outcome = self.bot.loop(vid_url, mode, amount)
        except Exception as exc:
            self._post_ui(self._on_run_failed, str(exc))
        else:
            self._post_ui(self._on_run_finished, outcome)

    def _on_run_finished(self, outcome):
        was_stopping = self.app_state is AppState.STOPPING
        if was_stopping and outcome == "stopped":
            self._append_log("Bot stopped")
        elif outcome == "rate_limited":
            self._append_log(
                "Run stopped safely because the service rate limit persisted. "
                "Wait at least 15-30 minutes before trying again."
            )
        self._finish_run()

    def _on_run_failed(self, message):
        self._append_log(f"Automation stopped after an unexpected error: {message}")
        self._finish_run()

    def _finish_run(self):
        if self.app_state is AppState.CLOSING:
            return

        if self._stats_after_id is not None:
            try:
                self.after_cancel(self._stats_after_id)
            except Exception:
                pass
            self._stats_after_id = None

        if hasattr(self, "start_time"):
            self.elapsed_time = time.time() - self.start_time

        self.link_entry.configure(state="normal")
        self.amount_entry.configure(state="normal")
        if self.mode_menu is not None:
            self.mode_menu.configure(state="normal")
        self.disclosure_checkbox.configure(state="normal")

        self._set_app_state(AppState.READY)
        if self.settings.disclosure_accepted:
            self.start_button.configure(
                text="Start", state="normal", command=self.start_bot
            )
        else:
            self.start_button.configure(
                text="Accept notice to continue", state="disabled"
            )

    def stop_bot(self):
        if self.app_state is not AppState.RUNNING:
            return

        self._set_app_state(AppState.STOPPING)
        self._append_log("Stopping bot...")
        self.bot.request_stop()
        self.start_button.configure(text="Stopping...", state="disabled")

    def update_stats_label(self, schedule_next=True):
        is_active = self.app_state in {AppState.RUNNING, AppState.STOPPING}
        if is_active and hasattr(self, "start_time"):
            elapsed_seconds = max(0, time.time() - self.start_time)
        else:
            elapsed_seconds = max(0, self.elapsed_time)
        time_elapsed = time.strftime("%H:%M:%S", time.gmtime(elapsed_seconds))

        counts = {
            "views": self.views,
            "hearts": self.hearts,
            "followers": self.followers,
            "shares": self.shares,
            "favorites": self.favorites,
        }
        for key, value in counts.items():
            self.stats_count_labels[key].configure(text=f"{value:,}")
        self.stats_total_value.configure(text=f"{sum(counts.values()):,}")

        status_labels = {
            AppState.IDLE: "Not set up",
            AppState.SETTING_UP: "Setting up",
            AppState.READY: "Ready",
            AppState.RUNNING: "Running",
            AppState.STOPPING: "Stopping",
            AppState.ERROR: "Needs attention",
            AppState.CLOSING: "Closing",
        }
        self.stats_progress_meta.configure(
            text=f"{status_labels[self.app_state]} · Elapsed {time_elapsed}"
        )

        if self.stats_mode and self.stats_target > 0:
            current_value = counts[self.stats_mode.lower()]
            progress = min(1.0, current_value / self.stats_target)
            percentage = round(progress * 100)
            self.stats_progress_value.configure(
                text=f"{current_value:,} / {self.stats_target:,}"
            )
            self.stats_progress.configure(progress_color=COLOR["success"])
            self.stats_progress.set(progress)
            self.stats_progress_title.configure(
                text=f"{self.stats_mode} target · {percentage}% complete"
            )
        else:
            self.stats_progress_value.configure(text="0 / —")
            self.stats_progress.configure(progress_color=COLOR["border"])
            self.stats_progress.set(0)
            self.stats_progress_title.configure(text="Start a run to track progress")

        if schedule_next and is_active:
            self._stats_after_id = self.after(1000, self.update_stats_label)
        elif not is_active:
            self._stats_after_id = None


def main() -> None:
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
