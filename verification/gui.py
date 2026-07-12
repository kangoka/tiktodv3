"""Offline GUI regression checks for the Windows CI runner."""

import json
import tempfile
import time
from pathlib import Path

from tiktodv3 import settings
from tiktodv3.gui import App, AppState
from tiktodv3.theme import COLOR, MIN_WINDOW_SIZE


def contrast_ratio(foreground, background):
    def luminance(value):
        channels = [int(value[index : index + 2], 16) / 255 for index in (1, 3, 5)]
        channels = [
            channel / 12.92
            if channel <= 0.04045
            else ((channel + 0.055) / 1.055) ** 2.4
            for channel in channels
        ]
        return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]

    lighter, darker = sorted(
        (luminance(foreground), luminance(background)), reverse=True
    )
    return (lighter + 0.05) / (darker + 0.05)


def pump_until(app, state, timeout=2):
    end = time.time() + timeout
    while app.app_state is state and time.time() < end:
        app.update()
        time.sleep(0.01)


def focus_chain(app):
    result = []
    widget = app
    for _ in range(30):
        name = str(app.tk.call("tk_focusNext", widget._w))
        if not name or name in result:
            break
        result.append(name)
        widget = app.nametowidget(name)
    return result


def check_theme_contrast():
    pairs = (
        ("accent_text", "accent"),
        ("text", "window"),
        ("text", "surface"),
        ("muted", "window"),
        ("warning_text", "warning_surface"),
        ("success", "surface_alt"),
    )
    for foreground, background in pairs:
        for theme_index in (0, 1):
            ratio = contrast_ratio(
                COLOR[foreground][theme_index], COLOR[background][theme_index]
            )
            assert ratio >= 4.5, (foreground, background, theme_index, ratio)


def main():
    settings_path = Path(tempfile.gettempdir()) / "tiktodv3-gui-verification.json"
    settings_path.write_text(
        json.dumps({"theme": "dark", "disclosure_accepted": False}),
        encoding="utf-8",
    )
    settings.SETTINGS_PATH = settings_path

    app = App()
    app.update()
    try:
        assert app.start_button.cget("state") == "disabled"
        assert app.log_text._textbox.cget("state") == "disabled"
        assert app.tab_view._segmented_button.winfo_height() >= 44  # noqa: SLF001
        assert app.stats_progress.get() == 0
        assert "Start a run" in app.stats_progress_title.cget("text")

        app.disclosure_checkbox.toggle()
        assert app.settings.disclosure_accepted
        assert app.start_button.cget("state") == "normal"

        app.bot.setup_bot = lambda: {  # type: ignore[method-assign]
            "available_modes": ("Views", "Followers"),
            "disabled_modes": frozenset(),
        }
        app.start_setup()
        pump_until(app, AppState.SETTING_UP)
        assert app.app_state is AppState.READY

        app.stats_mode = "Views"
        app.stats_target = 2000
        app.views = 1000
        app.hearts = 15
        app.followers = 2
        app.start_time = time.time() - 65
        app._set_app_state(AppState.RUNNING)
        app.update_stats_label(schedule_next=False)
        assert app.stats_progress.get() == 0.5
        assert app.stats_progress_value.cget("text") == "1,000 / 2,000"
        assert app.stats_count_labels["views"].cget("text") == "1,000"
        assert app.stats_total_value.cget("text") == "1,017"
        assert "00:01:05" in app.stats_progress_meta.cget("text")

        app.elapsed_time = 125
        app.app_state = AppState.READY
        app.update_stats_label(schedule_next=False)
        assert "00:02:05" in app.stats_progress_meta.cget("text")

        app.geometry("480x360")
        app.update()
        logical_size = app.geometry().split("+")[0]
        assert logical_size == f"{MIN_WINDOW_SIZE[0]}x{MIN_WINDOW_SIZE[1]}"
        assert app._stats_compact  # noqa: SLF001
        assert "Failures and limits" in app.stats_metrics_note.cget("text")

        chain = focus_chain(app)
        assert len(chain) >= 7, chain
        assert any("canvas" in item for item in chain), chain

        app.copy_log()
        assert app.clipboard_get()
        app.clear_log()
        assert "Log cleared" in app.log_text.get("1.0", "end")
        check_theme_contrast()
    finally:
        app.on_close()
        settings_path.unlink(missing_ok=True)

    print("GUI verification passed")


if __name__ == "__main__":
    main()
