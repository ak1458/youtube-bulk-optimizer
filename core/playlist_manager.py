import os
import csv
import json
import sys
import googleapiclient.errors
from core.oauth_handler import get_authenticated_service
from core.quota_manager import track_quota_usage

# Target Playlists Configuration
PLAYLISTS_CONFIG = {
    "VALORANT": {
        "title": "VALORANT | Tactical Action & Cinematic Highlights",
        "desc": "Cinematic Valorant gameplay, epic clutch highlights, and tactical ranked play with a peaceful yet engaging gaming vibe."
    },
    "FORZA_HORIZON": {
        "title": "Forza Horizon | Chill Driving & Scenic Roads",
        "desc": "Immersive and peaceful driving showcases through scenic roads, stunning visuals, and ultimate hypercar engines in Forza Horizon.",
        "existing_id": "PLA_xPD81J3eWKF1prH96hZ_vAVB4fR4mK"
    },
    "GTA_5": {
        "title": "GTA 5 | Los Santos Cinematic Exploration & Chaos",
        "desc": "Cinematic driving, realistic graphics mods, and fun open-world adventures in Grand Theft Auto V.",
        "existing_id": "PLA_xPD81J3eXduQU7IhaF-UdHRJ25-16N"
    },
    "RDR2": {
        "title": "Red Dead Redemption 2 | Cinematic & Peaceful Journeys",
        "desc": "Scenic open-world exploration, cinematic story highlights, and peaceful atmospheric walks in Red Dead Redemption 2."
    },
    "GOD_OF_WAR": {
        "title": "God of War | Epic Cinematic Battles & Lore",
        "desc": "Cinematic battles, young Kratos runs, and legendary story moments from the God of War series."
    },
    "CONTROL": {
        "title": "Control | Mind-Bending Sci-Fi Adventures",
        "desc": "Supernatural combat, surreal storylines, and high-action walkthroughs in Remedy's Control."
    },
    "DW_ORIGINS": {
        "title": "DW Origins | Massive Battles & Cinematic Legends",
        "desc": "Epic battlefield gameplay, character showcases, and massive combo action in Dynasty Warriors: Origins.",
        "existing_id": "PLA_xPD81J3eWpuZ1oZYY4mpGlklZ3z2dU"
    },
    "CREW_MOTORFEST": {
        "title": "The Crew Motorfest | Cruise & Racing Vibes",
        "desc": "Hypercar races, scenic cruises, and street racing action in The Crew Motorfest."
    },
    "RESIDENT_EVIL": {
        "title": "Resident Evil | Intense Survival Horror",
        "desc": "Survival horror walkthroughs, scary moments, and first blind playthroughs in Resident Evil Requiem."
    },
    "GENERAL_CINEMATIC": {
        "title": "Cinematic Gaming Journeys | Peaceful & Immersive",
        "desc": "A collection of visually stunning, immersive, and peaceful gameplay walkthroughs across various games."
    },
    "SHORTS": {
        "title": "Gaming Shorts | Chill & Epic Moments",
        "desc": "Quick gaming edits, funny moments, and epic gameplay highlights in under a minute."
    }
}

def determine_target_playlist(title, video_type, duration_sec):
    title_lower = title.lower()
    
    # Check if video is a Short
    if video_type == "Short" or duration_sec <= 61:
        return PLAYLISTS_CONFIG["SHORTS"]["title"]
        
    # Long video routing based on keywords
    if "valorant" in title_lower:
        return PLAYLISTS_CONFIG["VALORANT"]["title"]
    elif "forza" in title_lower:
        return PLAYLISTS_CONFIG["FORZA_HORIZON"]["title"]
    elif any(kw in title_lower for kw in ["gta", "grand theft auto", "los santos"]):
        return PLAYLISTS_CONFIG["GTA_5"]["title"]
    elif any(kw in title_lower for kw in ["rdr2", "red dead", "arthur morgan", "outlaw"]):
        return PLAYLISTS_CONFIG["RDR2"]["title"]
    elif any(kw in title_lower for kw in ["god of war", "kratos"]):
        return PLAYLISTS_CONFIG["GOD_OF_WAR"]["title"]
    elif "control" in title_lower:
        return PLAYLISTS_CONFIG["CONTROL"]["title"]
    elif any(kw in title_lower for kw in ["dynasty warriors", "origins", "dw"]):
        return PLAYLISTS_CONFIG["DW_ORIGINS"]["title"]
    elif "crew motorfest" in title_lower or "motorfest" in title_lower:
        return PLAYLISTS_CONFIG["CREW_MOTORFEST"]["title"]
    elif any(kw in title_lower for kw in ["resident evil", "re9", "requiem"]):
        return PLAYLISTS_CONFIG["RESIDENT_EVIL"]["title"]
    else:
        return PLAYLISTS_CONFIG["GENERAL_CINEMATIC"]["title"]

def load_sync_status():
    status_file = "playlist_sync_status.json"
    if os.path.exists(status_file):
        with open(status_file, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except Exception:
                pass
    return {"playlist_mappings": {}, "processed_videos": {}}

def save_sync_status(status):
    status_file = "playlist_sync_status.json"
    with open(status_file, "w", encoding="utf-8") as f:
        json.dump(status, f, indent=2)

def organize_youtube_playlists(csv_file='channel_analysis.csv', limit=100, dry_run=False, logger_callback=None):
    def log(msg):
        if logger_callback:
            logger_callback(msg)
        else:
            print(msg)
            sys.stdout.flush()

    if not os.path.exists(csv_file):
        log(f"Error: '{csv_file}' not found.")
        return False, 0

    sync_status = load_sync_status()
    playlist_mappings = sync_status.get("playlist_mappings", {})
    processed_videos = sync_status.get("processed_videos", {})

    # Seed mappings from config
    for key, p_conf in PLAYLISTS_CONFIG.items():
        if "existing_id" in p_conf and p_conf["title"] not in playlist_mappings:
            playlist_mappings[p_conf["title"]] = p_conf["existing_id"]

    # Read videos
    videos = []
    with open(csv_file, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            video_id = row.get("Video ID")
            title = row.get("Title", "")
            video_type = row.get("Type", "Long Video")
            try:
                duration_sec = float(row.get("Duration (sec)", 0))
            except ValueError:
                duration_sec = 0
            
            target_pl_title = determine_target_playlist(title, video_type, duration_sec)
            videos.append({
                "id": video_id,
                "title": title,
                "target_playlist": target_pl_title
            })

    log(f"Loaded {len(videos)} videos from channel analysis.")

    if dry_run:
        log("\n=== DRY RUN MODE: Showing Planned Changes ===")
        counts = {}
        for v in videos:
            t = v["target_playlist"]
            counts[t] = counts.get(t, 0) + 1
        for pl_title, cnt in counts.items():
            log(f"- Target Playlist: \"{pl_title}\" ➔ {cnt} videos planned.")
        log("=============================================\n")
        return False, 0

    log("Authenticating with YouTube API...")
    try:
        youtube = get_authenticated_service()
    except Exception as e:
        log(f"Authentication failed: {e}")
        return False, 0

    log("\nVerifying/Creating playlists (Ensuring Public status)...")
    try:
        live_playlists = {}
        next_page_token = None
        while True:
            res = youtube.playlists().list(
                mine=True,
                part="id,snippet",
                maxResults=50,
                pageToken=next_page_token
            ).execute()
            track_quota_usage(1)
            for item in res.get("items", []):
                live_playlists[item["id"]] = item["snippet"]["title"]
            next_page_token = res.get("nextPageToken")
            if not next_page_token:
                break
    except googleapiclient.errors.HttpError as e:
        content = e.content.decode('utf-8') if isinstance(e.content, bytes) else e.content
        log("Failed to fetch playlists from YouTube (Likely Quota Exceeded).")
        if "quotaExceeded" in content:
            return True, 0
        return False, 0

    live_title_to_id = {title: pl_id for pl_id, title in live_playlists.items()}

    # Create/update to make public
    for key, p_conf in PLAYLISTS_CONFIG.items():
        title = p_conf["title"]
        desc = p_conf["desc"]
        
        if title in live_title_to_id:
            pl_id = live_title_to_id[title]
            playlist_mappings[title] = pl_id
            try:
                youtube.playlists().update(
                    part="snippet,status",
                    body={
                        "id": pl_id,
                        "snippet": {"title": title, "description": desc},
                        "status": {"privacyStatus": "public"}
                    }
                ).execute()
                track_quota_usage(50)
            except Exception:
                pass
        elif "existing_id" in p_conf and p_conf["existing_id"] in live_playlists:
            pl_id = p_conf["existing_id"]
            try:
                youtube.playlists().update(
                    part="snippet,status",
                    body={
                        "id": pl_id,
                        "snippet": {"title": title, "description": desc},
                        "status": {"privacyStatus": "public"}
                    }
                ).execute()
                track_quota_usage(50)
                playlist_mappings[title] = pl_id
            except Exception:
                playlist_mappings[title] = pl_id
        else:
            try:
                new_pl = youtube.playlists().insert(
                    part="snippet,status",
                    body={
                        "snippet": {"title": title, "description": desc},
                        "status": {"privacyStatus": "public"}
                    }
                ).execute()
                track_quota_usage(50)
                playlist_mappings[title] = new_pl["id"]
            except Exception as e:
                log(f"Failed to create playlist '{title}': {e}")

    sync_status["playlist_mappings"] = playlist_mappings
    save_sync_status(sync_status)

    # Fetch existing items in all playlists
    playlist_contents = {}
    for pl_title, pl_id in playlist_mappings.items():
        playlist_contents[pl_id] = set()
        next_page_token = None
        try:
            while True:
                res = youtube.playlistItems().list(
                    playlistId=pl_id,
                    part="contentDetails",
                    maxResults=50,
                    pageToken=next_page_token
                ).execute()
                track_quota_usage(1)
                for item in res.get("items", []):
                    playlist_contents[pl_id].add(item["contentDetails"]["videoId"])
                next_page_token = res.get("nextPageToken")
                if not next_page_token:
                    break
        except Exception:
            pass

    # Add videos
    additions_made = 0
    quota_exceeded = False

    for v in videos:
        v_id = v["id"]
        target_pl_title = v["target_playlist"]
        pl_id = playlist_mappings.get(target_pl_title)

        if not pl_id:
            continue

        in_local_processed = v_id in processed_videos and pl_id in processed_videos[v_id]
        in_live_playlist = v_id in playlist_contents.get(pl_id, set())

        if in_local_processed or in_live_playlist:
            if v_id not in processed_videos:
                processed_videos[v_id] = []
            if pl_id not in processed_videos[v_id]:
                processed_videos[v_id].append(pl_id)
            continue

        if additions_made >= limit:
            log(f"Reached syncing limit of {limit} additions for this batch.")
            break

        log(f"Adding video {v_id} (\"{v['title'][:35]}...\") to \"{target_pl_title}\"...")
        try:
            youtube.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": pl_id,
                        "resourceId": {
                            "kind": "youtube#video",
                            "videoId": v_id
                        }
                    }
                }
            ).execute()
            track_quota_usage(50)
            
            if v_id not in processed_videos:
                processed_videos[v_id] = []
            processed_videos[v_id].append(pl_id)
            sync_status["processed_videos"] = processed_videos
            save_sync_status(sync_status)
            
            additions_made += 1
            
        except googleapiclient.errors.HttpError as e:
            content = e.content.decode('utf-8') if isinstance(e.content, bytes) else e.content
            log(f"Failed to add {v_id}: HTTP Error {e.resp.status}")
            if "quotaExceeded" in content:
                log("[ALERT] YouTube API Daily Quota Exceeded! Syncing paused.")
                quota_exceeded = True
                break
        except Exception as e:
            log(f"Failed to add {v_id}: {e}")

    log(f"Playlist organization batch completed. Total added: {additions_made} videos.")
    return quota_exceeded, additions_made
