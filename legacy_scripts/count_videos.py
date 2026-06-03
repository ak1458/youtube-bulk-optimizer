import os
import google_auth_oauthlib.flow
import googleapiclient.discovery

# Path to your client secrets
CLIENT_SECRETS_FILE = r"D:\gravity\Youtube Optimizer\YT bulk\client_secret.json"
SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]

def get_authenticated_service():
    if not os.path.exists(CLIENT_SECRETS_FILE):
        print(f"Error: Client secrets file not found at '{CLIENT_SECRETS_FILE}'.")
        return None

    # This will open a browser window for you to login and authorize the app
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, SCOPES)
    credentials = flow.run_local_server(port=0)
    youtube = googleapiclient.discovery.build(
        "youtube", "v3", credentials=credentials)
    return youtube

def main():
    print("Authenticating with YouTube API... Please check your browser!")
    youtube = get_authenticated_service()
    if not youtube:
        return

    print("\nAuthentication successful! Fetching your channel details...")
    
    # Get the authenticated user's channel details to find the 'uploads' playlist
    channels_response = youtube.channels().list(
        mine=True,
        part="contentDetails,statistics"
    ).execute()

    if not channels_response.get("items"):
        print("Could not find any channels for the authenticated user.")
        return

    channel = channels_response["items"][0]
    uploads_playlist_id = channel["contentDetails"]["relatedPlaylists"]["uploads"]
    total_videos_stat = channel["statistics"].get("videoCount", 0)

    print(f"Channel video count statistic: {total_videos_stat} videos.")
    print(f"Fetching your recent videos from the 'uploads' playlist (ID: {uploads_playlist_id})...")

    # Fetch up to 50 videos just to give a preview
    playlistitems_response = youtube.playlistItems().list(
        playlistId=uploads_playlist_id,
        part="snippet",
        maxResults=50
    ).execute()

    videos = playlistitems_response.get("items", [])
    
    print(f"\nSuccessfully retrieved metadata for {len(videos)} recent videos!")
    print("\nHere are your top 5 most recent videos:")
    for idx, item in enumerate(videos[:5]):
        title = item["snippet"]["title"]
        video_id = item["snippet"]["resourceId"]["videoId"]
        print(f"{idx + 1}. [ID: {video_id}] {title}")
        
    print(f"\nI can currently 'see' your entire library of {total_videos_stat} videos using the API.")

if __name__ == "__main__":
    main()
