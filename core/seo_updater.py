import os
import csv
import sys
import googleapiclient.errors
from core.oauth_handler import get_authenticated_service
from core.quota_manager import track_quota_usage

def update_youtube_seo(csv_file='videos_update.csv', limit=200, logger_callback=None):
    def log(msg):
        if logger_callback:
            logger_callback(msg)
        else:
            print(msg)
            sys.stdout.flush()

    if not os.path.exists(csv_file):
        log(f"Error: CSV file '{csv_file}' not found.")
        return False, 0

    log("Authenticating with YouTube API...")
    try:
        youtube = get_authenticated_service()
    except Exception as e:
        log(f"Authentication failed: {e}")
        return False, 0

    processed_count = 0
    quota_exceeded = False
    
    # Read rows
    rows = []
    with open(csv_file, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    log(f"Starting SEO updates (Limit: {limit} videos)...")

    for row in rows:
        if processed_count >= limit:
            log(f"Reached processing limit of {limit} videos for this batch.")
            break

        video_id = row.get('video_id')
        new_title = row.get('new_title')
        new_description = row.get('new_description')
        new_tags = row.get('tags', '')

        if not video_id:
            continue

        try:
            # 1. Fetch current details
            res = youtube.videos().list(
                part="snippet",
                id=video_id
            ).execute()
            track_quota_usage(1)

            if not res.get("items"):
                log(f"Failed: {video_id} - Video not found on YouTube.")
                continue

            video_item = res["items"][0]
            snippet = video_item["snippet"]

            changed = False
            
            # Compare title
            current_title = snippet.get("title", "")
            if new_title and current_title != new_title:
                snippet["title"] = new_title
                changed = True
                
            # Compare description
            current_description = snippet.get("description", "")
            if new_description and current_description != new_description:
                snippet["description"] = new_description
                changed = True
                
            # Compare tags
            new_tags_list = [tag.strip() for tag in new_tags.split(',')] if new_tags else []
            current_tags_list = snippet.get("tags", [])
            if sorted(new_tags_list) != sorted(current_tags_list):
                snippet["tags"] = new_tags_list
                changed = True
                
            # Compare category (20 = Gaming)
            if snippet.get("categoryId") != "20":
                snippet["categoryId"] = "20"
                changed = True

            if not changed:
                log(f"Skipping {video_id}: Already up-to-date on YouTube.")
                continue

            # 2. Perform live update
            youtube.videos().update(
                part="snippet",
                body={
                    "id": video_id,
                    "snippet": snippet
                }
            ).execute()
            track_quota_usage(50)

            log(f"Success: Updated metadata for {video_id}")
            processed_count += 1

        except googleapiclient.errors.HttpError as e:
            content = e.content.decode('utf-8') if isinstance(e.content, bytes) else e.content
            log(f"Failed: {video_id} - HTTP Error {e.resp.status}")
            if "quotaExceeded" in content:
                log("[ALERT] YouTube API Daily Quota Exceeded! SEO update paused.")
                quota_exceeded = True
                break
        except Exception as e:
            log(f"Failed: {video_id} - Unexpected error: {str(e)}")

    log(f"SEO update batch completed. Total updated: {processed_count} videos.")
    return quota_exceeded, processed_count
