from time import time
from collections import deque
from threading import Lock

class RateLimiter:
    def __init__(self):
        self.short_window = deque()  # 10 requests per second
        self.long_window = deque()   # 100 requests per 120 seconds
        self.lock = Lock()
        
        # Configure limits
        self.short_limit = 8
        self.short_window_seconds = 1
        self.long_limit = 90
        self.long_window_seconds = 120

    def can_make_request(self) -> bool:
        """Check if a request can be made based on rate limits."""
        current_time = time()
        
        with self.lock:
            # Remove expired timestamps from windows
            while self.short_window and self.short_window[0] <= current_time - self.short_window_seconds:
                self.short_window.popleft()
            while self.long_window and self.long_window[0] <= current_time - self.long_window_seconds:
                self.long_window.popleft()
            
            # Check if adding a new request would exceed either limit
            if (len(self.short_window) >= self.short_limit or 
                len(self.long_window) >= self.long_limit):
                return False
            
            # Add the new timestamp to both windows
            self.short_window.append(current_time)
            self.long_window.append(current_time)
            return True

    def wait_for_available_request(self) -> None:
        """Wait until a request can be made."""
        while not self.can_make_request():
            time.sleep(0.1)