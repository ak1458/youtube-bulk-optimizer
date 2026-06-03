import os
import google.oauth2.credentials
import googleapiclient.discovery

CLIENT_SECRETS_FILE = r"D:\gravity\Youtube Optimizer\YT bulk\client_secret.json"
SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]

def main():
    token_file = "token.json"
    if not os.path.exists(token_file):
        print("Error: token.json not found. Please authenticate first.")
        return

    creds = google.oauth2.credentials.Credentials.from_authorized_user_file(token_file, SCOPES)
    youtube = googleapiclient.discovery.build("youtube", "v3", credentials=creds)

    try:
        response = youtube.channels().list(
            mine=True,
            part="snippet"
        ).execute()

        if response.get("items"):
            channel_name = response["items"][0]["snippet"]["title"]
            channel_id = response["items"][0]["id"]
            print(f"AUTHENTICATED_CHANNEL_NAME: {channel_name}")
            print(f"AUTHENTICATED_CHANNEL_ID: {channel_id}")
        else:
            print("No channel found for these credentials.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
