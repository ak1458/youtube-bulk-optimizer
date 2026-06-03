import os
import csv
import json
import sys
import time
import threading
import webbrowser
import googleapiclient.errors
from flask import Flask, jsonify, render_template, request


# Reconfigure stdout for UTF-8 to prevent console print errors on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Import our core components
from core.seo_filter import filter_csv_metadata
from core.seo_updater import update_youtube_seo
from core.playlist_manager import organize_youtube_playlists
from core.scheduler import AutoRescheduler
from core.oauth_handler import get_authenticated_service
from core.quota_manager import get_quota_status, track_quota_usage


app = Flask(__name__)

# Active background tasks tracking
tasks = {}
tasks_lock = threading.Lock()
rescheduler = AutoRescheduler()

class ThreadedTask:
    def __init__(self, target_func, task_type, args=(), kwargs={}):
        self.target_func = target_func
        self.task_type = task_type # 'playlist_sync' or 'seo_update'
        self.args = args
        self.kwargs = kwargs
        self.status = "running"
        self.logs = []
        self.lock = threading.Lock()
        self.thread = threading.Thread(target=self._run)
        self.thread.daemon = True
        self.thread.start()

    def log(self, message):
        with self.lock:
            self.logs.append(message)

    def _run(self):
        try:
            # Inject our logging callback
            run_kwargs = self.kwargs.copy()
            run_kwargs['logger_callback'] = self.log
            
            quota_exceeded, processed = self.target_func(*self.args, **run_kwargs)
            
            if quota_exceeded:
                self.status = "quota_exceeded"
                self.log(f"[SCHEDULER] Hit quota limit. Scheduling auto-resume...")
                
                # Reschedule this exact operation
                res_time, seconds = rescheduler.schedule_resume(self._resume_callback)
                self.log(f"[SCHEDULER] Auto-resume scheduled at {res_time} ({int(seconds // 3600)}h {int((seconds % 3600) // 60)}m remaining).")
            else:
                self.status = "done"
        except Exception as e:
            self.status = "failed"
            self.log(f"Execution failed: {str(e)}")

    def _resume_callback(self):
        global tasks
        # Determine unique task ID
        new_task_id = f"{self.task_type}_resumed_{int(time.time())}"
        self.log(f"[SCHEDULER] Quota reset time reached. Launching resumed task: {new_task_id}...")
        
        with tasks_lock:
            # Restart the background task
            tasks[new_task_id] = ThreadedTask(self.target_func, self.task_type, self.args, self.kwargs)

    def get_new_logs(self, last_index):
        with self.lock:
            if last_index < len(self.logs):
                new_logs = self.logs[last_index:]
                return new_logs, len(self.logs)
            return [], last_index

@app.route('/')
def home():
    return render_template('index.html')

def format_subs(subs_str):
    try:
        count = int(subs_str)
        if count >= 1000000:
            return f"{count / 1000000:.1f}M"
        elif count >= 1000:
            return f"{count / 1000:.1f}K"
        return str(count)
    except Exception:
        return subs_str

@app.route('/api/stats', methods=['GET'])
def get_stats():
    # 1. Total channel counts from channel_analysis.csv
    total_videos = 0
    long_videos = 0
    shorts = 0
    
    analysis_file = 'channel_analysis.csv'
    if os.path.exists(analysis_file):
        with open(analysis_file, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                total_videos += 1
                if row.get('Type') == 'Short':
                    shorts += 1
                else:
                    long_videos += 1

    # 2. Sync progress from playlist_sync_status.json
    playlist_synced = 0
    status_file = 'playlist_sync_status.json'
    if os.path.exists(status_file):
        try:
            with open(status_file, 'r', encoding='utf-8') as f:
                sync_data = json.load(f)
                playlist_synced = len(sync_data.get('processed_videos', {}))
        except Exception:
            pass

    # 3. Pending SEO count and list from videos_update.csv
    pending_seo_count = 0
    pending_videos = []
    
    update_file = 'videos_update.csv'
    if os.path.exists(update_file):
        with open(update_file, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                v_id = row.get('video_id')
                curr_title = row.get('current_title', '')
                curr_desc = row.get('current_description', '')
                new_title = row.get('new_title', '')
                new_desc = row.get('new_description', '')
                tags = row.get('tags', '')
                
                # A video is pending if we've flagged it for change (i.e. new != current)
                if (new_title != curr_title) or (new_desc != curr_desc):
                    pending_seo_count += 1
                    pending_videos.append({
                        "video_id": v_id,
                        "current_title": curr_title,
                        "current_description": curr_desc,
                        "new_title": new_title,
                        "new_description": new_desc,
                        "tags": tags
                    })

    # Get scheduler status
    scheduler_status = rescheduler.get_status()

    # Get dynamic channel details & local quota usage
    used_quota, remaining_quota = get_quota_status()
    channel_name = "Not Connected"
    channel_logo = ""
    channel_subs = "0"
    authenticated = False
    
    try:
        youtube = get_authenticated_service()
        ch_res = youtube.channels().list(mine=True, part="snippet,statistics").execute()
        track_quota_usage(1)
        used_quota, remaining_quota = get_quota_status() # Refresh after decrementing
        if ch_res.get("items"):
            item = ch_res["items"][0]
            channel_name = item["snippet"]["title"]
            channel_logo = item["snippet"]["thumbnails"]["default"]["url"]
            channel_subs = format_subs(item["statistics"].get("subscriberCount", "0"))
            authenticated = True
    except googleapiclient.errors.HttpError as e:
        content = e.content.decode('utf-8') if isinstance(e.content, bytes) else e.content
        if "quotaExceeded" in content:
            print("YouTube API Quota exceeded during channel stats fetch.")
            authenticated = True
            channel_name = "Authenticated (Quota Exceeded)"
            track_quota_usage(10000) # Force local usage to max
            used_quota, remaining_quota = 10000, 0
        else:
            print(f"HTTP Error fetching channel details: {e}")
    except Exception as e:
        print(f"Error fetching channel details: {e}")


    return jsonify({
        "total_videos": total_videos,
        "long_videos": long_videos,
        "shorts": shorts,
        "playlist_synced": playlist_synced,
        "pending_seo_count": pending_seo_count,
        "pending_videos": pending_videos,
        "scheduler": scheduler_status,
        "channel": {
            "name": channel_name,
            "logo": channel_logo,
            "subs": channel_subs,
            "authenticated": authenticated
        },
        "quota": {
            "used": used_quota,
            "remaining": remaining_quota,
            "limit": 10000
        }
    })


@app.route('/api/save-metadata', methods=['POST'])
def save_metadata():
    try:
        updated_videos = request.get_json()
        if not isinstance(updated_videos, list):
            return jsonify({"status": "error", "message": "Invalid payload format."}), 400

        # Save to CSV
        update_file = 'videos_update.csv'
        if not os.path.exists(update_file):
            return jsonify({"status": "error", "message": "videos_update.csv does not exist."}), 404

        rows = []
        with open(update_file, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)

        updated_map = {v['video_id']: v for v in updated_videos}
        for row in rows:
            v_id = row['video_id']
            if v_id in updated_map:
                row['new_title'] = updated_map[v_id]['new_title']
                row['new_description'] = updated_map[v_id]['new_description']
                row['tags'] = updated_map[v_id]['tags']

        with open(update_file, mode='w', encoding='utf-8', newline='') as f:
            fieldnames = ["video_id", "current_title", "current_description", "current_tags", "new_title", "new_description", "tags"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        # Run filtering again to ensure updates are clean
        filter_csv_metadata(update_file)

        return jsonify({"status": "success", "message": "CSV updated and filtered successfully!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/sync-playlists', methods=['POST'])
def sync_playlists():
    data = request.get_json() or {}
    dry_run = data.get("dry_run", False)
    limit = data.get("limit", 100)

    # Cancel any active scheduled task when user manually starts
    rescheduler.cancel()

    task_id = "playlist_sync"
    with tasks_lock:
        if task_id in tasks and tasks[task_id].status == "running":
            return jsonify({"status": "error", "message": "A playlist sync task is already running."}), 400
        
        # Start direct python task inside ThreadedTask
        tasks[task_id] = ThreadedTask(
            target_func=organize_youtube_playlists,
            task_type="playlist_sync",
            kwargs={"limit": limit, "dry_run": dry_run}
        )

    return jsonify({"status": "success", "task_id": task_id})

@app.route('/api/update-seo', methods=['POST'])
def update_seo():
    # Cancel any active scheduled task when user manually starts
    rescheduler.cancel()

    task_id = "seo_update"
    with tasks_lock:
        if task_id in tasks and tasks[task_id].status == "running":
            return jsonify({"status": "error", "message": "An SEO update task is already running."}), 400
        
        # Start direct python task inside ThreadedTask
        tasks[task_id] = ThreadedTask(
            target_func=update_youtube_seo,
            task_type="seo_update",
            kwargs={"limit": 200}
        )

    return jsonify({"status": "success", "task_id": task_id})

poll_indexes = {}
poll_indexes_lock = threading.Lock()

@app.route('/api/task-status', methods=['GET'])
def task_status():
    task_id = request.args.get("task_id")
    if not task_id:
        return jsonify({"status": "error", "message": "Missing task_id"}), 400

    # Locate task. If it's a resumed task, we check for the latest active resumed task
    with tasks_lock:
        task = tasks.get(task_id)
        if not task:
            # Check if there is a resumed task active
            resumed_keys = [k for k in tasks.keys() if k.startswith(task_id) and k != task_id]
            if resumed_keys:
                latest_resumed = sorted(resumed_keys)[-1]
                task = tasks[latest_resumed]
                task_id = latest_resumed

    if not task:
        return jsonify({"status": "error", "message": "Task not found"}), 404

    with poll_indexes_lock:
        last_index = poll_indexes.get(task_id, 0)
        new_logs, next_index = task.get_new_logs(last_index)
        poll_indexes[task_id] = next_index

    if task.status not in ["running", "quota_exceeded"] and next_index >= len(task.logs):
        with poll_indexes_lock:
            poll_indexes[task_id] = 0

    return jsonify({
        "status": task.status,
        "logs": new_logs
    })

@app.route('/api/cancel-resume', methods=['POST'])
def cancel_resume():
    rescheduler.cancel()
    return jsonify({"status": "success", "message": "Auto-resume timer cancelled."})

def open_browser():
    webbrowser.open("http://localhost:5000")

if __name__ == '__main__':
    # Initial filter on start to keep metadata updates clean
    filter_csv_metadata('videos_update.csv')
    
    # Start browser opener
    threading.Timer(1.5, open_browser).start()
    
    # Run Flask server locally
    app.run(host='localhost', port=5000, debug=False)
