import subprocess
import sys
import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class RestartHandler(FileSystemEventHandler):
    def __init__(self):
        self.process = None
        self.start_server()

    def start_server(self):
        if self.process:
            self.process.kill()
            time.sleep(1)
        print("◈ STARTING JARVIS...")
        self.process = subprocess.Popen(
            ['python3', 'app.py'],
            cwd=os.path.expanduser('~/jarvis-app')
        )
        print("✓ JARVIS ONLINE")

    def on_modified(self, event):
        if event.src_path.endswith('app.py'):
            print(f"◈ app.py CHANGED — RESTARTING...")
            time.sleep(0.5)
            self.start_server()

if __name__ == '__main__':
    path = os.path.expanduser('~/jarvis-app')
    handler = RestartHandler()
    observer = Observer()
    observer.schedule(handler, path, recursive=False)
    observer.start()
    print(f"◈ WATCHING {path} FOR CHANGES...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        if handler.process:
            handler.process.kill()
    observer.join()
