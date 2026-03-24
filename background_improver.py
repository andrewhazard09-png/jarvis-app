import threading
import time
import requests
import json
import os
import shutil
import subprocess
from datetime import datetime

GROQ_KEY = None
try:
    from config import GROQ_KEY
except:
    pass

BACKUP_DIR = os.path.expanduser('~/jarvis-app/backups')
LOG_FILE = os.path.expanduser('~/jarvis-app/auto_improve.log')
CONV_LOG = os.path.expanduser('~/jarvis-app/conversations.log')

def log(msg):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_FILE, 'a') as f:
        f.write(f'[{timestamp}] {msg}\n')

def backup():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    src = os.path.expanduser('~/jarvis-app/app.py')
    dst = f'{BACKUP_DIR}/app_{timestamp}.py'
    shutil.copy(src, dst)
    return dst

def syntax_check(filepath):
    result = subprocess.run(
        ['python3', '-m', 'py_compile', filepath],
        capture_output=True, text=True
    )
    return result.returncode == 0

def get_recent_convos():
    if not os.path.exists(CONV_LOG):
        return ""
    with open(CONV_LOG) as f:
        lines = f.readlines()
    return ''.join(lines[-20:])

def ask_groq(prompt):
    if not GROQ_KEY:
        return None
    try:
        res = requests.post('https://api.groq.com/openai/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {GROQ_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'llama-3.1-8b-instant',
                'messages': [{'role': 'user', 'content': prompt}],
                'max_tokens': 512
            },
            timeout=30
        )
        return res.json()['choices'][0]['message']['content']
    except:
        return None

def try_improve():
    try:
        log('Starting improvement cycle...')

        # Get recent conversations
        convos = get_recent_convos()
        if not convos:
            log('No conversations yet, skipping.')
            return

        # Read current code
        current = open(os.path.expanduser('~/jarvis-app/app.py')).read()

        # Ask Groq for one small improvement
        suggestion = ask_groq(f"""You are improving a Flask AI assistant called JARVIS.

Recent conversations:
{convos}

Current app.py (first 1500 chars):
{current[:1500]}

Identify ONE small bug or improvement based on the conversations.
Respond with ONLY valid Python code to add or change, under 10 lines.
If no improvement needed respond with exactly: NO_CHANGE""")

        if not suggestion or 'NO_CHANGE' in suggestion or len(suggestion) < 10:
            log('No improvement needed this cycle.')
            return

        log(f'Improvement identified: {suggestion[:100]}')

        # Write to temp file first
        temp_path = os.path.expanduser('~/jarvis-app/app_temp.py')
        shutil.copy(os.path.expanduser('~/jarvis-app/app.py'), temp_path)

        # Append improvement as a comment for now — safe approach
        with open(temp_path, 'a') as f:
            f.write(f'\n# AUTO-IMPROVEMENT [{datetime.now().isoformat()}]\n# {suggestion[:200]}\n')

        # Syntax check temp file
        if not syntax_check(temp_path):
            log('Syntax check failed — discarding, keeping original.')
            os.remove(temp_path)
            return

        # All good — backup and apply
        backup_path = backup()
        log(f'Backed up to {backup_path}')

        shutil.copy(temp_path, os.path.expanduser('~/jarvis-app/app.py'))
        os.remove(temp_path)
        log('Improvement applied successfully.')

    except Exception as e:
        log(f'Improvement cycle failed silently: {str(e)}')

def run_background_improver():
    log('Background improver started.')
    while True:
        time.sleep(600)  # Run every 10 minutes
        try:
            try_improve()
        except:
            pass  # Never crash, always silent

def start():
    t = threading.Thread(target=run_background_improver, daemon=True)
    t.start()
