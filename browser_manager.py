import subprocess
import tempfile
import os
import shutil
import time
import requests
from dotenv import load_dotenv

load_dotenv()
CHROME_PATH = os.environ.get("CHROME_PATH", r"C:\Program Files\Google\Chrome\Application\chrome.exe")
CDP_PORT = 9222

class BrowserManager:
    def __init__(self):
        self.process = None
        self.temp_dir = None

    def start_chrome(self) -> str:
        """
        Starts Chrome with CDP enabled using a temporary isolated profile.
        Returns the websocket URL for CDP connection.
        """
        # Kiểm tra xem Chrome CDP đã mở trước đó hay chưa
        try:
            response = requests.get(f"http://localhost:{CDP_PORT}/json/version", timeout=1)
            if response.status_code == 200:
                ws_url = response.json().get("webSocketDebuggerUrl")
                if ws_url:
                    self.process = None # Đánh dấu không phải tiến trình mình tạo ra
                    return ws_url
        except requests.exceptions.RequestException:
            pass

        self.temp_dir = tempfile.mkdtemp(prefix="chrome_playwright_profile_")
        
        args = [
            CHROME_PATH,
            f"--remote-debugging-port={CDP_PORT}",
            f"--user-data-dir={self.temp_dir}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-background-networking",
            "--disable-sync",
            "--disable-translate",
            "--lang=en-US",
        ]
        
        self.process = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Wait for CDP endpoint to be ready
        for _ in range(10):
            try:
                response = requests.get(f"http://localhost:{CDP_PORT}/json/version", timeout=1)
                if response.status_code == 200:
                    ws_url = response.json().get("webSocketDebuggerUrl")
                    if ws_url:
                        return ws_url
            except requests.exceptions.RequestException:
                pass
            time.sleep(0.5)
            
        raise Exception("Failed to start Chrome CDP endpoint.")

    def stop_chrome(self):
        """Stops Chrome and cleans up the temporary profile."""
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
        
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                time.sleep(1) # Ensure file locks are released
                shutil.rmtree(self.temp_dir, ignore_errors=True)
            except Exception as e:
                pass
