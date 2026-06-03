import json
import os
import datetime

QUOTA_FILE = "quota_usage.json"
DAILY_LIMIT = 10000

def get_quota_status():
    now = datetime.datetime.now(datetime.timezone.utc)
    
    # Next reset is today at 8:00 AM UTC (or tomorrow if we're past it)
    reset_time = now.replace(hour=8, minute=0, second=0, microsecond=0)
    if now >= reset_time:
        reset_time += datetime.timedelta(days=1)
        
    data = {"used": 0, "last_reset": now.isoformat()}
    if os.path.exists(QUOTA_FILE):
        try:
            with open(QUOTA_FILE, "r") as f:
                data = json.load(f)
        except Exception:
            pass
            
    # Calculate most recent reset point (e.g. today at 8:00 AM UTC, or yesterday if now < 8:00 AM)
    recent_reset = now.replace(hour=8, minute=0, second=0, microsecond=0)
    if now < recent_reset:
        recent_reset -= datetime.timedelta(days=1)
        
    # If last reset was before the most recent reset point, we reset the quota to 0
    try:
        last_reset_dt = datetime.datetime.fromisoformat(data["last_reset"])
        if last_reset_dt < recent_reset:
            data["used"] = 0
            data["last_reset"] = now.isoformat()
            with open(QUOTA_FILE, "w") as f:
                json.dump(data, f, indent=2)
    except Exception:
        # Fallback reset if parsing fails
        data["used"] = 0
        data["last_reset"] = now.isoformat()
        with open(QUOTA_FILE, "w") as f:
            json.dump(data, f, indent=2)
            
    remaining = max(0, DAILY_LIMIT - data["used"])
    return data["used"], remaining

def track_quota_usage(units):
    used, remaining = get_quota_status()
    data = {
        "used": min(DAILY_LIMIT, used + units),
        "last_reset": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    with open(QUOTA_FILE, "w") as f:
        json.dump(data, f, indent=2)
