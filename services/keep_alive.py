import os
import time
import threading
import logging
import requests

logger = logging.getLogger(__name__)

_ping_thread_started = False
_lock = threading.Lock()

def start_keep_alive(app=None):
    """
    Starts a background daemon thread that pings the application's health endpoint
    every 5 minutes (300 seconds) to prevent Render free tier instances from sleeping.
    """
    global _ping_thread_started

    with _lock:
        if _ping_thread_started:
            return
        _ping_thread_started = True

    # Disable keep-alive in test environments
    if os.getenv('FLASK_ENV') == 'testing' or (app and app.config.get('TESTING')):
        return

    ping_url = os.getenv('PING_URL') or os.getenv('RENDER_EXTERNAL_URL')
    if not ping_url:
        ping_url = 'https://ech-efmm.onrender.com'

    ping_url = ping_url.rstrip('/')
    if not ping_url.endswith('/health'):
        ping_url = f"{ping_url}/health"

    interval = int(os.getenv('PING_INTERVAL', 300))  # Default 5 minutes (300 seconds)

    def ping_loop():
        # Initial pause to let the web server start up fully
        time.sleep(10)
        logger.info(f"[KeepAlive] Pinger started. Target: {ping_url}, Interval: {interval}s")
        
        while True:
            try:
                response = requests.get(ping_url, timeout=15)
                logger.info(f"[KeepAlive] Ping to {ping_url} succeeded with status {response.status_code}")
            except Exception as e:
                logger.warning(f"[KeepAlive] Ping to {ping_url} failed: {e}")
            time.sleep(interval)

    thread = threading.Thread(target=ping_loop, daemon=True, name="KeepAlivePinger")
    thread.start()
