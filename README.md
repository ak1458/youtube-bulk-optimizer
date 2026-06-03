# 📺 YouTube Bulk SEO & Playlist Organizer Hub

A high-performance, developer-centric desktop dashboard designed to automate bulk YouTube video SEO optimization and playlist categorization. Built with a solid, high-contrast, matte-minimalist theme (2026 design standard), this tool displays live channel diagnostics and manages the strict YouTube API daily quota limits (10,000 units) with zone-aware auto-rescheduling.

---

## ✨ Features

### 1. 📂 Intelligent Playlist Auto-Organizer
* **Automated Playlist Creation**: Maps all long-form gaming videos into descriptive, game-specific playlists (e.g. *Forza Horizon*, *GTA 5*, *Red Dead Redemption 2*, etc.) based on keywords.
* **Shorts Categorization**: Groups all short-form videos (less than 60 seconds) into a separate, dedicated playlist (*Gaming Shorts | Chill & Epic Moments*).
* **Public Settings Enforcement**: Automatically updates newly created or mapped playlists to be **Public** rather than private.
* **Batch Processing Limits**: Restricts bulk uploads via customizable batches (e.g., 5, 50, 100, 150) to prevent hitting quota bounds instantly.

### 2. ⚡ Selective SEO Publisher
* **Delta Metadata Updates**: Scans and optimizes only "0-SEO" videos (those with empty descriptions and simple, default titles).
* **Intelligent Title & Description Appends**: Injects highly optimized cinematic titles, comprehensive descriptions (social links, PC specs, tags), and hashtags while leaving already optimized videos untouched.
* **Inline CSV Metadata Editor**: Review, modify, and save optimized metadata updates to the CSV directly from the dashboard before publishing live to YouTube.

### 3. 🔋 Local API Quota Manager & Rescheduler
* **Real-time Quota Meter**: Tracks local API unit consumption out of the daily 10,000 unit limit (1 unit for list operations, 50 units for playlist creation/addition/video updates).
* **Auto-Resume Scheduling**: If a quota limits threshold is exceeded, the scheduler automatically freezes operations, calculates the countdown to the daily UTC reset (8:00 AM UTC / 1:30 PM IST), and starts a background daemon that resumes the remaining queue immediately upon reset.
* **Cancelable Actions**: Users can manually terminate or reset the auto-run background timer with a click.

### 4. 🎛️ Matte Minimalist 2026 UX
* **Pure Clean Dark Interface**: Built with solid `#0a0b0d` backgrounds, dark slate panels, high-contrast thin borders, and sharp accent tags. Zero gradients, zero blurs, zero neon glows.
* **Dynamic Channel widget**: Automatically fetches the logo, custom name, and subscriber count of the authenticated channel in real-time, removing all hardcoded placeholders.
* **Live Console Output Stream**: Streams detailed diagnostic logs directly into the interface's embedded terminal log as background operations execute.

---

## 🛠️ Project Directory Tree

```
D:\gravity\Youtube Optimizer\YT bulk\
├── core\
│   ├── oauth_handler.py     # Secure Google OAuth handler & token refresher
│   ├── playlist_manager.py  # Playlist creation, visibility, and batch video mappings
│   ├── quota_manager.py     # Local daily quota usage state tracker (quota_usage.json)
│   ├── scheduler.py         # Thread-safe auto-reschedule countdown timer
│   ├── seo_filter.py        # Isolates low-SEO videos based on metadata criteria
│   └── seo_updater.py       # Publishes title, description, and tags to YouTube
├── static\
│   └── style.css            # 2026 Minimalist CSS stylesheet
├── templates\
│   └── index.html           # Single-page control panel UI
├── legacy_scripts\          # Archived developmental scripts (cleanup storage)
├── app.py                   # Main Flask server entrypoint
├── requirements.txt         # Package dependencies
└── README.md                # Technical documentation
```

---

## 🚀 Setup & Installation

### Prerequisite: Obtain YouTube API Credentials
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a project, enable the **YouTube Data API v3**, and configure the OAuth Consent Screen.
3. Generate an **OAuth Client ID** credential (type: Desktop App).
4. Download the JSON credential file, rename it to `client_secret.json`, and place it in the root folder of this project.

### Run the Dashboard
1. Clone this repository locally.
2. Install the requirements:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python app.py
   ```
4. The dashboard will automatically open in your default browser at `http://localhost:5000`.

---

## 🔌 API Quota Pricing Reference
The local quota manager tracks consumption based on standard Google Cloud Billing guidelines:
* **`youtube.channels().list`**: 1 unit
* **`youtube.videos().list`**: 1 unit
* **`youtube.playlists().list`**: 1 unit
* **`youtube.playlistItems().list`**: 1 unit
* **`youtube.playlists().insert` / `update`**: 50 units
* **`youtube.playlistItems().insert`**: 50 units
* **`youtube.videos().update`**: 50 units
