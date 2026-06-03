import datetime
import threading
import time

class AutoRescheduler:
    def __init__(self):
        self.timer = None
        self.scheduled_time = None
        self.callback = None
        self.lock = threading.Lock()

    def get_seconds_until_quota_reset(self):
        now = datetime.datetime.now(datetime.timezone.utc)
        # Quota resets at 8:00 AM UTC daily
        reset_time = now.replace(hour=8, minute=0, second=0, microsecond=0)
        if now >= reset_time:
            reset_time += datetime.timedelta(days=1)
        return (reset_time - now).total_seconds(), reset_time

    def schedule_resume(self, callback_func):
        with self.lock:
            # Cancel any existing timer
            if self.timer:
                self.timer.cancel()
                
            seconds, reset_dt = self.get_seconds_until_quota_reset()
            
            # Convert reset_dt (UTC) to local time for display
            local_dt = reset_dt.astimezone()
            self.scheduled_time = local_dt.strftime("%Y-%m-%d %I:%M:%S %p %Z")
            self.callback = callback_func
            
            # Create a threading.Timer
            self.timer = threading.Timer(seconds, self._trigger)
            self.timer.daemon = True
            self.timer.start()
            
            return self.scheduled_time, seconds

    def _trigger(self):
        with self.lock:
            self.timer = None
            self.scheduled_time = None
            cb = self.callback
            
        if cb:
            print(f"[SCHEDULER] Quota reset time reached. Triggering background sync...")
            cb()

    def cancel(self):
        with self.lock:
            if self.timer:
                self.timer.cancel()
                self.timer = None
            self.scheduled_time = None

    def get_status(self):
        with self.lock:
            if self.timer:
                seconds, _ = self.get_seconds_until_quota_reset()
                hours = int(seconds // 3600)
                minutes = int((seconds % 3600) // 60)
                countdown_str = f"{hours}h {minutes}m remaining"
                return {
                    "is_scheduled": True,
                    "scheduled_at": self.scheduled_time,
                    "countdown": countdown_str
                }
            return {
                "is_scheduled": False,
                "scheduled_at": None,
                "countdown": None
            }
