import os
import csv
import json
import re
import sys
import argparse
import google.oauth2.credentials
import google.auth.transport.requests
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors

# Reconfigure stdout for UTF-8 to prevent console print errors on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

CLIENT_SECRETS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "client_secret.json")
SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]

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

def get_authenticated_service():
    creds = None
    token_file = "token.json"
    if os.path.exists(token_file):
        creds = google.oauth2.credentials.Credentials.from_authorized_user_file(token_file, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(google.auth.transport.requests.Request())
            except Exception as e:
                print(f"Error refreshing token: {e}")
                creds = None
        if not creds:
            if not os.path.exists(CLIENT_SECRETS_FILE):
                print(f"Error: Client secrets file not found at '{CLIENT_SECRETS_FILE}'.")
                return None
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRETS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_file, "w") as token:
            token.write(creds.to_json())
    return googleapiclient.discovery.build("youtube", "v3", credentials=creds)

def load_sync_status():
    status_file = "playlist_sync_status.json"
    if os.path.exists(status_file):
        with open(status_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"playlist_mappings": {}, "processed_videos": {}}

def save_sync_status(status):
    status_file = "playlist_sync_status.json"
    with open(status_file, "w", encoding="utf-8") as f:
        json.dump(status, f, indent=2)

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

def main():
    parser = argparse.ArgumentParser(description="Organize YouTube videos into playlists.")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without modifying playlists.")
    parser.add_argument("--limit", type=int, default=100, help="Maximum number of video playlist additions in this run.")
    args = parser.parse_args()

    csv_file = "channel_analysis.csv"
    if not os.path.exists(csv_file):
        print(f"Error: '{csv_file}' not found. Please run analyze_videos.py first.")
        return

    # Load sync status
    sync_status = load_sync_status()
    playlist_mappings = sync_status.get("playlist_mappings", {})
    processed_videos = sync_status.get("processed_videos", {})

    # Seed mappings with existing/known playlist IDs from config
    for key, p_conf in PLAYLISTS_CONFIG.items():
        if "existing_id" in p_conf and p_conf["title"] not in playlist_mappings:
            playlist_mappings[p_conf["title"]] = p_conf["existing_id"]

    # Read videos from channel_analysis.csv
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

    print(f"Total videos to organize: {len(videos)}")

    if args.dry_run:
        print("\n=== DRY RUN MODE: Showing Planned Changes ===")
        # Count target playlist distributions
        counts = {}
        for v in videos:
            t = v["target_playlist"]
            counts[t] = counts.get(t, 0) + 1
        for pl_title, cnt in counts.items():
            print(f"- Target Playlist: \"{pl_title}\" -> {cnt} videos planned.")
        print("=============================================\n")
        return

    # Live Mode
    print("Authenticating with YouTube API...")
    youtube = get_authenticated_service()
    if not youtube:
        print("Authentication failed.")
        return

    # 1. Verify/Create/Rename Playlists
    print("\nVerifying/Creating playlists...")
    
    # Fetch all channel playlists again to ensure we have the latest titles/IDs
    live_playlists = {}
    next_page_token = None
    while True:
        res = youtube.playlists().list(
            mine=True,
            part="id,snippet",
            maxResults=50,
            pageToken=next_page_token
        ).execute()
        for item in res.get("items", []):
            live_playlists[item["id"]] = item["snippet"]["title"]
        next_page_token = res.get("nextPageToken")
        if not next_page_token:
            break

    # Build active map of playlist title to ID
    live_title_to_id = {title: pl_id for pl_id, title in live_playlists.items()}

    # Create/update playlists based on PLAYLISTS_CONFIG
    for key, p_conf in PLAYLISTS_CONFIG.items():
        title = p_conf["title"]
        desc = p_conf["desc"]
        
        # If the playlist exists under its exact name
        if title in live_title_to_id:
            pl_id = live_title_to_id[title]
            playlist_mappings[title] = pl_id
            print(f"  - Playlist exists: \"{title}\" (ID: {pl_id}). Ensuring it is public...")
            try:
                youtube.playlists().update(
                    part="snippet,status",
                    body={
                        "id": pl_id,
                        "snippet": {
                            "title": title,
                            "description": desc
                        },
                        "status": {
                            "privacyStatus": "public"
                        }
                    }
                ).execute()
            except Exception as e:
                print(f"    Failed to ensure public status: {e}")
        # Else check if we have a mapped existing_id that we should rename
        elif "existing_id" in p_conf and p_conf["existing_id"] in live_playlists:
            pl_id = p_conf["existing_id"]
            old_title = live_playlists[pl_id]
            print(f"  - Renaming existing playlist \"{old_title}\" to \"{title}\" and making public...")
            try:
                youtube.playlists().update(
                    part="snippet,status",
                    body={
                        "id": pl_id,
                        "snippet": {
                            "title": title,
                            "description": desc
                        },
                        "status": {
                            "privacyStatus": "public"
                        }
                    }
                ).execute()
                playlist_mappings[title] = pl_id
                print(f"    Renamed successfully! ID: {pl_id}")
            except Exception as e:
                print(f"    Failed to rename: {e}")
                playlist_mappings[title] = pl_id
        # Otherwise, create a new playlist
        else:
            print(f"  - Creating new public playlist: \"{title}\"...")
            try:
                new_pl = youtube.playlists().insert(
                    part="snippet,status",
                    body={
                        "snippet": {
                            "title": title,
                            "description": desc
                        },
                        "status": {
                            "privacyStatus": "public"
                        }
                    }
                ).execute()
                pl_id = new_pl["id"]
                playlist_mappings[title] = pl_id
                print(f"    Created successfully! ID: {pl_id}")
            except Exception as e:
                print(f"    Failed to create playlist: {e}")

    sync_status["playlist_mappings"] = playlist_mappings
    save_sync_status(sync_status)

    # 2. Fetch existing items in all playlists to prevent duplicate additions
    print("\nFetching existing items in playlists to prevent duplicates...")
    playlist_contents = {}
    for pl_title, pl_id in playlist_mappings.items():
        playlist_contents[pl_id] = set()
        print(f"  - Fetching items for: \"{pl_title}\"...")
        next_page_token = None
        try:
            while True:
                res = youtube.playlistItems().list(
                    playlistId=pl_id,
                    part="contentDetails",
                    maxResults=50,
                    pageToken=next_page_token
                ).execute()
                for item in res.get("items", []):
                    v_id = item["contentDetails"]["videoId"]
                    playlist_contents[pl_id].add(v_id)
                next_page_token = res.get("nextPageToken")
                if not next_page_token:
                    break
            print(f"    Found {len(playlist_contents[pl_id])} existing videos in playlist.")
        except Exception as e:
            print(f"    Error fetching playlist items: {e}")

    # 3. Add videos to playlists (up to the limit)
    print(f"\nAdding videos to playlists (limit: {args.limit} additions for this run)...")
    additions_made = 0
    skipped_count = 0
    quota_exceeded = False

    for v in videos:
        v_id = v["id"]
        target_pl_title = v["target_playlist"]
        pl_id = playlist_mappings.get(target_pl_title)

        if not pl_id:
            print(f"  - Skipping {v_id}: Target playlist ID not found for \"{target_pl_title}\"")
            continue

        # Check if video is already in the playlist according to local status or live status
        in_local_processed = v_id in processed_videos and pl_id in processed_videos[v_id]
        in_live_playlist = v_id in playlist_contents.get(pl_id, set())

        if in_local_processed or in_live_playlist:
            # Update local state if missing
            if v_id not in processed_videos:
                processed_videos[v_id] = []
            if pl_id not in processed_videos[v_id]:
                processed_videos[v_id].append(pl_id)
            skipped_count += 1
            continue

        if additions_made >= args.limit:
            print(f"\nReached the limit of {args.limit} additions for this run. Stopping.")
            break

        print(f"  - Adding video {v_id} (\"{v['title'][:40]}...\") to \"{target_pl_title}\"...")
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
            
            # Save progress
            if v_id not in processed_videos:
                processed_videos[v_id] = []
            processed_videos[v_id].append(pl_id)
            sync_status["processed_videos"] = processed_videos
            save_sync_status(sync_status)
            
            additions_made += 1
            
        except googleapiclient.errors.HttpError as e:
            content = e.content.decode('utf-8') if isinstance(e.content, bytes) else e.content
            print(f"    Failed: HTTP Error {e.resp.status}: {content}")
            if "quotaExceeded" in content:
                print("    [ALERT] YouTube API Daily Quota Exceeded! Stopping execution.")
                quota_exceeded = True
                break
        except Exception as e:
            print(f"    Failed: {e}")

    print(f"\nPlaylist Organization Summary:")
    print(f"  - Additions made in this run: {additions_made}")
    print(f"  - Videos already in target playlists (skipped): {skipped_count}")
    
    if quota_exceeded:
        print("  - Status: Paused due to YouTube API Daily Quota Exceeded. Please run again tomorrow.")
    elif additions_made == 0:
        print("  - Status: All videos are fully organized in their respective playlists!")
    else:
        print(f"  - Status: Partially processed. Run the script again to process the next batch of {args.limit} videos.")

if __name__ == "__main__":
    main()
