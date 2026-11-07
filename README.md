# YouTube Bulk Optimizer

A local Flask dashboard for organizing playlists and reviewing bulk video metadata updates through the YouTube Data API.

[![Python: Backend](https://img.shields.io/badge/Python-Backend-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org)
[![Flask: Dashboard](https://img.shields.io/badge/Flask-Dashboard-334155?style=flat-square&logo=flask&logoColor=white)](app.py)
[![YouTube: Data API](https://img.shields.io/badge/YouTube-Data%20API-FF0000?style=flat-square&logo=youtube&logoColor=white)](https://developers.google.com/youtube)
[![License: Proprietary](https://img.shields.io/badge/License-Proprietary-64748B?style=flat-square)](LICENSE)

[Application](app.py) · [API documentation](https://developers.google.com/youtube/v3)

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

## License

Copyright © 2026 Ashraf Kamal. Reuse is restricted by [LICENSE](LICENSE).
