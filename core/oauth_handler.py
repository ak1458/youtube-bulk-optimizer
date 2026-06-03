import os
import google.oauth2.credentials
import google.auth.transport.requests
import google_auth_oauthlib.flow
import googleapiclient.discovery

SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
CLIENT_SECRETS_FILE = "client_secret.json"

def get_authenticated_service(token_file="token.json"):
    creds = None
    
    # Check in current working directory
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
                # Search up one directory level if running from inside core/
                alt_path = os.path.join("..", CLIENT_SECRETS_FILE)
                if os.path.exists(alt_path):
                    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(alt_path, SCOPES)
                else:
                    raise FileNotFoundError(f"Client secrets file not found at '{CLIENT_SECRETS_FILE}'.")
            else:
                flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
                
            creds = flow.run_local_server(port=0)
            
        with open(token_file, "w") as token:
            token.write(creds.to_json())

    youtube = googleapiclient.discovery.build("youtube", "v3", credentials=creds)
    return youtube
