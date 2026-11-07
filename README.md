<p align="center"><img src=".github/assets/readme-header.svg" alt="YouTube Bulk Optimizer — Review metadata changes · Organize playlists · Track batches" width="100%" /></p>

# YouTube Bulk Optimizer

YouTube Bulk Optimizer is a local Flask administration dashboard for an authorized YouTube channel. It organizes videos into keyword-based playlists, filters metadata for review, reads edited CSV data, and submits selected batches through the YouTube Data API. Quota state and resume scheduling are tracked locally. Because these operations can modify a real channel, the important workflow is inspection and deliberate publication rather than a claim that the tool guarantees ranking improvements.

[![Stars](https://img.shields.io/github/stars/ak1458/youtube-bulk-optimizer?style=flat-square)](https://github.com/ak1458/youtube-bulk-optimizer/stargazers)
[![Watching](https://img.shields.io/github/watchers/ak1458/youtube-bulk-optimizer?style=flat-square&label=watching)](https://github.com/ak1458/youtube-bulk-optimizer/watchers)
[![Forks](https://img.shields.io/github/forks/ak1458/youtube-bulk-optimizer?style=flat-square)](https://github.com/ak1458/youtube-bulk-optimizer/forks)
[![Activity](https://img.shields.io/github/last-commit/ak1458/youtube-bulk-optimizer?style=flat-square)](https://github.com/ak1458/youtube-bulk-optimizer/activity)
[![License: Proprietary](https://img.shields.io/badge/License-Proprietary-64748b?style=flat-square)](LICENSE)

**[How it works](#how-it-works) · [Run locally](#run-locally) · [Configuration](#configuration) · [Commands](#development-commands) · [Versions](#versions-and-distribution) · [License](#license)**

## How it works

1. Configure the desktop OAuth client and authorize the intended YouTube account.
2. Load the channel/video information and inspect the selected metadata or playlist task.
3. Review the CSV and batch selection before starting API writes.
4. Inspect logs and remaining local quota estimates; confirm provider-side results after a batch completes.

## Architecture

| Path | Purpose |
| --- | --- |
| [app.py](<app.py>) | Flask dashboard and operation handlers. |
| [core/oauth_handler.py](<core/oauth_handler.py>) | OAuth token handling and refresh. |
| [core/playlist_manager.py](<core/playlist_manager.py>) | Playlist classification and API changes. |
| [core/seo_filter.py](<core/seo_filter.py>) | Candidate selection rules. |
| [core/seo_updater.py](<core/seo_updater.py>) | Video metadata write logic. |
| [core/quota_manager.py](<core/quota_manager.py>) | Local quota accounting. |
| [core/scheduler.py](<core/scheduler.py>) | In-process deferred operation scheduling. |

## What it does

- Organizes videos into keyword-based playlists.
- Filters videos for metadata review and edits CSV-based update data.
- Runs batch API operations with local quota tracking and scheduling.
- Displays progress and logs in a browser dashboard.

## Run locally

```bash
git clone https://github.com/ak1458/youtube-bulk-optimizer.git
cd youtube-bulk-optimizer
python -m venv .venv
# Activate .venv for your shell, then:
python -m pip install -r requirements.txt
python app.py
```

Enable the YouTube Data API in your Google project and place the desktop OAuth client configuration in `client_secret.json` as expected by `core/oauth_handler.py`. Complete authorization in the browser. Keep credentials, tokens, channel exports, and quota files out of commits.

## Engineering notes

| Module | Responsibility |
| --- | --- |
| `core/oauth_handler.py` | Google authorization |
| `core/playlist_manager.py` | Playlist operations |
| `core/seo_filter.py`, `core/seo_updater.py` | Metadata selection and updates |
| `core/quota_manager.py`, `core/scheduler.py` | Local quota state and scheduling |

The dashboard is a local administration tool. Publishing metadata and playlist actions modify the authorized channel; review the selected batch first. The local quota estimate is not the provider's authoritative quota usage, and optimized wording does not guarantee views or rankings.


## Configuration

There is no root environment template in this snapshot. Follow the linked setup documentation and the module that consumes each setting. Keep credentials server-side and use development or sandbox accounts while validating an integration.

## Development commands

Use the Python/launcher instructions in the setup section and the linked documentation. No root npm script set is defined for this application.

These are available commands, not a claim that all checks passed in this documentation pass. Connected checks require the services, credentials, and isolated data described above.

## Operational notes

Inspect the writer before using it on a nongaming channel: the current metadata-update path sets category 20 (Gaming) and can replace or clear tags according to the input. The resume scheduler runs in process; it is not a durable queue across application shutdowns. Local quota tracking is an estimate, not an authoritative read of Google’s account-wide consumption. Keep downloaded OAuth credentials, refreshed tokens, and channel exports untracked.

## Troubleshooting

| Symptom | What to check |
| --- | --- |
| Authorization is refused | Confirm the correct desktop client, enabled API, consent/test-user configuration, and intended account. |
| A scheduled batch never resumes | Keep the local process running and inspect scheduler/log state; restarting the app does not imply durable job recovery. |
| Metadata changed unexpectedly | Compare the selected CSV, category assignment, and tags against seo_updater.py before another write batch. |

## Versions and distribution

No published GitHub Release or version tag was recorded in this snapshot. The default branch is a development/source snapshot; it must not be described as a stable downloadable release merely to populate the sidebar.

GitHub Packages is a separate registry. This README does not imply that a registry package exists; use the installation path documented here rather than an invented package-install command.

## Documentation and maintenance

- [core/seo_updater.py](<core/seo_updater.py>)
- [core/oauth_handler.py](<core/oauth_handler.py>)
- [legacy_scripts/NEXT_STEPS.md](<legacy_scripts/NEXT_STEPS.md>)

For change proposals, see [CONTRIBUTING.md](CONTRIBUTING.md). Include the affected workflow, reproduction steps, and relevant check output when reporting a problem. Do not include credentials or live customer data.

## License

This repository’s project code is **proprietary / all rights reserved**. Public visibility does not grant unrestricted reuse. Read [LICENSE](<LICENSE>) for the exact terms. Third-party dependencies and bundled components retain their own notices.
