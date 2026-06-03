import os
import csv
import google.oauth2.credentials
import google.auth.transport.requests
import google_auth_oauthlib.flow
import googleapiclient.discovery

CLIENT_SECRETS_FILE = r"D:\gravity\Youtube Optimizer\YT bulk\client_secret.json"
SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]

def get_authenticated_service():
    creds = None
    token_file = "token_readonly.json"
    
    if os.path.exists(token_file):
        creds = google.oauth2.credentials.Credentials.from_authorized_user_file(token_file, SCOPES)
        
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(google.auth.transport.requests.Request())
            except Exception:
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

    youtube = googleapiclient.discovery.build("youtube", "v3", credentials=creds)
    return youtube

def main():
    print("Authenticating...")
    youtube = get_authenticated_service()
    if not youtube:
        return

    print("Fetching channel details...")
    channels_response = youtube.channels().list(
        mine=True,
        part="contentDetails,statistics"
    ).execute()

    if not channels_response.get("items"):
        print("Could not find any channels.")
        return

    channel = channels_response["items"][0]
    uploads_playlist_id = channel["contentDetails"]["relatedPlaylists"]["uploads"]
    
    print(f"Fetching ALL videos from the 'uploads' playlist (ID: {uploads_playlist_id})...")
    
    video_ids = []
    next_page_token = None
    
    # Fetch all video IDs from the uploads playlist
    while True:
        playlistitems_response = youtube.playlistItems().list(
            playlistId=uploads_playlist_id,
            part="contentDetails",
            maxResults=50,
            pageToken=next_page_token
        ).execute()

        for item in playlistitems_response.get("items", []):
            video_ids.append(item["contentDetails"]["videoId"])
            
        next_page_token = playlistitems_response.get("nextPageToken")
        if not next_page_token:
            break

    print(f"Found {len(video_ids)} total videos. Now fetching detailed metadata in batches...")
    
    all_videos_data = []
    
    # Fetch details for videos in batches of 50
    for i in range(0, len(video_ids), 50):
        batch_ids = video_ids[i:i+50]
        videos_response = youtube.videos().list(
            id=",".join(batch_ids),
            part="snippet,contentDetails"
        ).execute()
        
        for video in videos_response.get("items", []):
            snippet = video["snippet"]
            content_details = video["contentDetails"]
            
            video_id = video["id"]
            title = snippet.get("title", "")
            description = snippet.get("description", "")
            tags = snippet.get("tags", [])
            category_id = snippet.get("categoryId", "")
            
            # Parse duration using custom regex
            duration_iso = content_details.get("duration", "PT0S")
            try:
                import re
                match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_iso)
                if match:
                    hours = int(match.group(1)) if match.group(1) else 0
                    minutes = int(match.group(2)) if match.group(2) else 0
                    seconds = int(match.group(3)) if match.group(3) else 0
                    duration_sec = hours * 3600 + minutes * 60 + seconds
                else:
                    duration_sec = 0
            except Exception:
                duration_sec = 0
                
            video_type = "Short" if duration_sec <= 61 else "Long Video"
            
            hashtags_count = description.count("#")
            
            all_videos_data.append({
                "Video ID": video_id,
                "Type": video_type,
                "Title": title,
                "Has Description": "Yes" if description.strip() else "No",
                "Description Length": len(description),
                "Hashtags Count": hashtags_count,
                "Tags Count": len(tags),
                "Category ID": category_id,
                "Duration (sec)": duration_sec,
                "Published At": snippet.get("publishedAt", "")
            })
            
    # Write to CSV
    csv_filename = "channel_analysis.csv"
    with open(csv_filename, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            "Video ID", "Type", "Title", "Has Description", "Description Length", 
            "Hashtags Count", "Tags Count", "Category ID", "Duration (sec)", "Published At"
        ])
        writer.writeheader()
        writer.writerows(all_videos_data)
        
    print(f"\nAnalysis complete! Saved data for {len(all_videos_data)} videos to {csv_filename}.")
    
    # Summary
    long_videos = [v for v in all_videos_data if v["Type"] == "Long Video"]
    shorts = [v for v in all_videos_data if v["Type"] == "Short"]
    
    no_desc = [v for v in all_videos_data if v["Has Description"] == "No"]
    no_tags = [v for v in all_videos_data if v["Tags Count"] == 0]
    no_hashtags = [v for v in all_videos_data if v["Hashtags Count"] == 0]
    
    print("\n--- SEO ANALYSIS SUMMARY ---")
    print(f"Total Videos Analyzed: {len(all_videos_data)}")
    print(f"  - Long Videos: {len(long_videos)}")
    print(f"  - Shorts: {len(shorts)}")
    print(f"Videos with NO Description: {len(no_desc)}")
    print(f"Videos with 0 Tags: {len(no_tags)}")
    print(f"Videos with 0 Hashtags: {len(no_hashtags)}")
    print("\nNext step: Open channel_analysis.csv to review the exact videos.")

if __name__ == "__main__":
    main()
