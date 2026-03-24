import subprocess
import time
import json
import os
from datetime import datetime
from memory import add_pattern

WATCH_LOG = os.path.expanduser('~/jarvis-app/activity.log')

def get_active_app():
    result = subprocess.run([
        'osascript', '-e',
        'tell application "System Events" to get name of first application process whose frontmost is true'
    ], capture_output=True, text=True)
    return result.stdout.strip()

def log_activity():
    app = get_active_app()
    hour = datetime.now().hour
    entry = {"app": app, "hour": hour, "time": datetime.now().isoformat()}
    with open(WATCH_LOG, 'a') as f:
        f.write(json.dumps(entry) + '\n')
    return app, hour

def analyze_patterns():
    if not os.path.exists(WATCH_LOG):
        return
    with open(WATCH_LOG) as f:
        lines = f.readlines()
    
    from collections import Counter
    apps = Counter()
    for line in lines[-100:]:
        try:
            entry = json.loads(line)
            apps[entry['app']] += 1
        except:
            pass
    
    top_apps = apps.most_common(3)
    if top_apps:
        pattern = f"Most used apps: {', '.join(f'{a}({c}x)' for a,c in top_apps)}"
        add_pattern(pattern)
        print(f'◈ PATTERN DETECTED: {pattern}')

if __name__ == '__main__':
    print('◈ COMPUTER WATCHING STARTED...')
    count = 0
    while True:
        try:
            app, hour = log_activity()
            count += 1
            if count % 60 == 0:
                analyze_patterns()
                print(f'◈ ANALYZED 60 SAMPLES — patterns updated')
        except Exception as e:
            pass
        time.sleep(60)
