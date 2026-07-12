"""Persistent user preference storage."""

import json
from dataclasses import asdict, dataclass
from pathlib import Path

SETTINGS_PATH = Path.home() / ".tiktodv3" / "settings.json"


@dataclass
class AppSettings:
    theme: str = "dark"
    disclosure_accepted: bool = False

    @classmethod
    def load(cls):
        try:
            data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            return cls()

        theme = data.get("theme", "dark")
        if theme not in {"light", "dark"}:
            theme = "dark"
        return cls(
            theme=theme,
            disclosure_accepted=bool(data.get("disclosure_accepted", False)),
        )

    def save(self):
        try:
            SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
            SETTINGS_PATH.write_text(
                json.dumps(asdict(self), indent=2) + "\n", encoding="utf-8"
            )
        except OSError:
            # Preferences are helpful but must never block the application.
            return
