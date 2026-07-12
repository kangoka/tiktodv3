# Changelog

## Unreleased

### Changed

- Organized runtime modules under the `tiktodv3` package, offline checks under
  `verification`, and build implementations under `scripts`.
- Preserved the original root launch, verification, and build commands through
  thin compatibility wrappers.

## 2.0.0 — 2026-07-12

### Added

- Added an explicit `IDLE → SETTING_UP → READY → RUNNING → STOPPING` application
  state model.
- Added automatic supported-mode discovery and clear disabled-mode feedback.
- Added confirmed progress callbacks, a Stats view, elapsed-time reporting, and
  copyable read-only logs.
- Added a target-progress dashboard with confirmed/target values, percentage,
  per-mode session totals, live run status, and responsive number formatting.
- Added light and dark themes with persisted preferences.
- Added keyboard navigation and shortcuts for setup/start/stop, mode selection,
  theme switching, log focus, and repository access.
- Added a first-run authorization, data-use, and privacy-risk acknowledgment.
- Added dependency preflight checks with actionable Tesseract and browser errors.
- Added deterministic root verification scripts, Ruff and Mypy configuration,
  SHA-pinned CI, security guidance, and reproducible executable build tooling.
- Added local versioned EXE packaging with a SHA-256 checksum for releases.
- Licensed the project under Apache-2.0 and documented direct third-party
  component notices.

### Fixed

- Prevented Followers runs from continuing forever because of a missing counter.
- Prevented failed, busy, and timed-out submissions from being counted as sent.
- Added TikTok URL and positive-amount validation.
- Prevented failed or duplicate Setup operations from leaking browser resources.
- Moved all Tk updates to the main thread and bounded worker shutdown.
- Replaced unbounded automation retries with a three-failure circuit breaker.
- Fixed resource lookup when launching outside the project directory.
- Prevented the first CAPTCHA solve from OCRing a visible loading placeholder.
  CAPTCHA images must now be stable, non-placeholder images before OCR runs.
- Rejected placeholder OCR such as `loading` and invalid CAPTCHA-shaped output.
- Detected `Too many requests`/`Please slow down` as a dedicated remote rate-limit
  state so it is never counted as a send or consumed as a generic page failure.
- Added a 90-180 second randomized rate-limit pause and a safe stop after three
  consecutive rate-limit checks to avoid continuously hammering the service.

### Changed

- Added semantic selectors with legacy selector fallbacks and state-based waits.
- Processed CAPTCHA images in memory instead of writing `captcha.png`.
- Added dependency preflight checks and actionable setup failures.
- Added an explicit application state model and thread-safe progress callbacks.
- Redesigned the GUI for keyboard access, responsive minimum sizing, accessible
  contrast, persistent themes, read-only logs, and clearer status feedback.
- Added a first-run authorization, data-use, and privacy-risk acknowledgment.
- Added deterministic verification, lint configuration, CI, security guidance,
  and executable build documentation.
- Separated browser automation from the Tk GUI and kept Playwright operations on
  their owning worker thread.
- Centralized application metadata, mode configuration, selectors, limits, and
  timing policy in `config.py`.
- Replaced brittle fixed delays with state polling and semantic selector fallbacks.
- Release builds now run verification, compilation, formatting, lint, and type
  checks before PyInstaller creates the executable.
- Refined the Stats information hierarchy and raised the Log/Stats tab target to
  the application's 44 px control standard.

### Security and resilience

- Added cooperative cancellation, bounded browser shutdown, and cleanup after
  failed or duplicate setup operations.
- Avoided persistent CAPTCHA files and documented the local/third-party data
  boundary.
- Added cautious handling for remote throttling without proxy rotation or other
  attempts to evade a service restriction.

## 1.2.0 — 2025-01-26

- Added amount limits and updated the browser automation integration.
