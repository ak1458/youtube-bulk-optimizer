import os
import google.oauth2.credentials
import google.auth.transport.requests
import google_auth_oauthlib.flow
import googleapiclient.discovery

CLIENT_SECRETS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "client_secret.json")
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

    youtube = googleapiclient.discovery.build("youtube", "v3", credentials=creds)
    return youtube

def main():
    youtube = get_authenticated_service()
    if not youtube:
        print("Failed to authenticate.")
        return

    print("Fetching playlists...")
    playlists = []
    next_page_token = None
    while True:
        res = youtube.playlists().list(
            mine=True,
            part="snippet,contentDetails",
            maxResults=50,
            pageToken=next_page_token
        ).execute()
        for item in res.get("items", []):
            playlists.append({
                "id": item["id"],
                "title": item["snippet"]["title"],
                "item_count": item["contentDetails"]["itemCount"]
            })
        next_page_token = res.get("nextPageToken")
        if not next_page_token:
            break

    print(f"Found {len(playlists)} playlists:")
    for pl in playlists:
        print(f"- {pl['title']} (ID: {pl['id']}, Items: {pl['item_count']})")

if __name__ == "__main__":
    main()
