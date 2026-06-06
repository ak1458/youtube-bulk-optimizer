import os
import csv
import google.oauth2.credentials
import google.auth.transport.requests
import google_auth_oauthlib.flow
import googleapiclient.discovery

CLIENT_SECRETS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "client_secret.json")
SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]

def get_authenticated_service():
    creds = None
    token_file = "token.json"
    
    # Check if we already have a saved token
    if os.path.exists(token_file):
        creds = google.oauth2.credentials.Credentials.from_authorized_user_file(token_file, SCOPES)
        
    # If there are no (valid) credentials available, let the user log in
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
            
        # Save the credentials for the next run
        with open(token_file, "w") as token:
            token.write(creds.to_json())

    youtube = googleapiclient.discovery.build(
        "youtube", "v3", credentials=creds)
    return youtube

def get_video_tags(youtube, video_ids):
    """Fetches tags and other detailed metadata for a list of video IDs (max 50)."""
    tags_dict = {}
    try:
        response = youtube.videos().list(
            part="snippet",
            id=",".join(video_ids)
        ).execute()

        for item in response.get("items", []):
            video_id = item["id"]
            tags = item["snippet"].get("tags", [])
            tags_dict[video_id] = ", ".join(tags)
    except Exception as e:
        print(f"Error fetching tags: {e}")
    return tags_dict

def main():
    print("Authenticating with YouTube API...")
    youtube = get_authenticated_service()
    if not youtube:
        return

    print("Authentication successful! Fetching channel details...")
    channels_response = youtube.channels().list(
        mine=True,
        part="contentDetails"
    ).execute()

    if not channels_response.get("items"):
        print("Could not find any channels.")
        return

    uploads_playlist_id = channels_response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    
    print(f"Fetching all videos from uploads playlist ({uploads_playlist_id})...")
    
    videos = []
    next_page_token = None

    while True:
        playlistitems_response = youtube.playlistItems().list(
            playlistId=uploads_playlist_id,
            part="snippet",
            maxResults=50,
            pageToken=next_page_token
        ).execute()

        for item in playlistitems_response.get("items", []):
            video_id = item["snippet"]["resourceId"]["videoId"]
            title = item["snippet"]["title"]
            description = item["snippet"]["description"]
            
            # Avoid fetching deleted/private videos
            if title in ["Deleted video", "Private video"]:
                continue

            videos.append({
                "video_id": video_id,
                "current_title": title,
                "current_description": description
            })

        next_page_token = playlistitems_response.get("nextPageToken")
        if not next_page_token:
            break

    print(f"Found {len(videos)} active videos. Now fetching tags for them in batches...")

    # Fetch tags in batches of 50
    for i in range(0, len(videos), 50):
        batch = videos[i:i+50]
        video_ids = [v["video_id"] for v in batch]
        tags_dict = get_video_tags(youtube, video_ids)
        
        for v in batch:
            v["current_tags"] = tags_dict.get(v["video_id"], "")

    output_csv = "videos_update.csv"
    print(f"Exporting to '{output_csv}'...")

    with open(output_csv, mode='w', encoding='utf-8', newline='') as file:
        fieldnames = ["video_id", "current_title", "current_description", "current_tags", "new_title", "new_description", "tags"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        
        writer.writeheader()
        for v in videos:
            writer.writerow({
                "video_id": v["video_id"],
                "current_title": v["current_title"],
                "current_description": v["current_description"],
                "current_tags": v["current_tags"],
                "new_title": v["current_title"],
                "new_description": v["current_description"],
                "tags": v["current_tags"]
            })

    print(f"Done! Created '{output_csv}' with all {len(videos)} videos.")
    print("You can now open this CSV file, edit the 'new_title', 'new_description', and 'tags' columns, and then run 'update_videos.py'.")

if __name__ == "__main__":
    main()
