import os
import sys
import google.oauth2.credentials
import google.auth.transport.requests
import google_auth_oauthlib.flow
import googleapiclient.discovery

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

CLIENT_SECRETS_FILE = r"D:\gravity\Youtube Optimizer\YT bulk\client_secret.json"
SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]

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
                creds = None
        if not creds:
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRETS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_file, "w") as token:
            token.write(creds.to_json())
    return googleapiclient.discovery.build("youtube", "v3", credentials=creds)

def main():
    youtube = get_authenticated_service()
    if not youtube:
        return

    # First get playlists
    playlists_res = youtube.playlists().list(
        mine=True,
        part="id,snippet",
        maxResults=50
    ).execute()
    
    playlists = playlists_res.get("items", [])
    playlist_video_map = {}
    
    for pl in playlists:
        pl_id = pl["id"]
        pl_title = pl["snippet"]["title"]
        print(f"\nFetching items for playlist: {pl_title} ({pl_id})...")
        
        video_ids = []
        next_page_token = None
        while True:
            res = youtube.playlistItems().list(
                playlistId=pl_id,
                part="contentDetails,snippet",
                maxResults=50,
                pageToken=next_page_token
            ).execute()
            
            for item in res.get("items", []):
                v_id = item["contentDetails"]["videoId"]
                title = item["snippet"]["title"]
                video_ids.append(v_id)
                print(f"  - {v_id}: {title}")
                
            next_page_token = res.get("nextPageToken")
            if not next_page_token:
                break
        playlist_video_map[pl_id] = video_ids

if __name__ == "__main__":
    main()
