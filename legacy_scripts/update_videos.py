import os
import csv
import google.oauth2.credentials
import google.auth.transport.requests
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors

CLIENT_SECRETS_FILE = r"D:\gravity\Youtube Optimizer\YT bulk\client_secret.json"
SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
MAX_VIDEOS_PER_RUN = 200

def get_authenticated_service():
    """Authenticates the user and returns a YouTube Data API v3 service object."""
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

def main():
    youtube = get_authenticated_service()
    if not youtube:
        return

    csv_file = 'videos_update.csv'
    if not os.path.exists(csv_file):
        print(f"Error: CSV file '{csv_file}' not found in the current directory.")
        return

    processed_count = 0

    with open(csv_file, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        for row in reader:
            if processed_count >= MAX_VIDEOS_PER_RUN:
                print(f"Reached maximum limit of {MAX_VIDEOS_PER_RUN} videos for this run. Stopping to prevent quota limit.")
                break

            video_id = row.get('video_id')
            new_title = row.get('new_title')
            new_description = row.get('new_description')
            new_tags = row.get('tags', '')

            if not video_id:
                print("Skipping row with missing video_id.")
                continue

            try:
                # 1. Fetch the existing video to get the snippet
                videos_list_response = youtube.videos().list(
                    part="snippet",
                    id=video_id
                ).execute()

                if not videos_list_response.get("items"):
                    print(f"Failed: {video_id} - Video not found on YouTube.")
                    continue

                video_item = videos_list_response["items"][0]
                snippet = video_item["snippet"]

                # Compare fields to determine if we actually need to update
                changed = False
                
                # Check title
                current_title = snippet.get("title", "")
                if new_title and current_title != new_title:
                    snippet["title"] = new_title
                    changed = True
                    
                # Check description
                current_description = snippet.get("description", "")
                if new_description and current_description != new_description:
                    snippet["description"] = new_description
                    changed = True
                    
                # Check tags
                new_tags_list = [tag.strip() for tag in new_tags.split(',')] if new_tags else []
                current_tags_list = snippet.get("tags", [])
                if sorted(new_tags_list) != sorted(current_tags_list):
                    snippet["tags"] = new_tags_list
                    changed = True
                    
                # Check category ID
                current_category = snippet.get("categoryId", "")
                if current_category != "20":
                    snippet["categoryId"] = "20"
                    changed = True

                if not changed:
                    print(f"Skipping {video_id}: Already up-to-date on YouTube.")
                    continue

                # 2. Update the video on YouTube
                youtube.videos().update(
                    part="snippet",
                    body={
                        "id": video_id,
                        "snippet": snippet
                    }
                ).execute()

                print(f"Success: {video_id}")
                processed_count += 1

            except googleapiclient.errors.HttpError as e:
                print(f"Failed: {video_id} - HTTP Error {e.resp.status}: {e.content.decode('utf-8') if isinstance(e.content, bytes) else e.content}")
            except Exception as e:
                print(f"Failed: {video_id} - Unexpected error: {str(e)}")

    print(f"\nCompleted! Successfully processed {processed_count} videos.")

if __name__ == "__main__":
    main()
