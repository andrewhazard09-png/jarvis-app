import json
import os
import requests
import datetime
import shutil
import schedule
import time

LOG_FILE = os.path.expanduser('~/jarvis-app/conversations.json')
REPORT_FILE = os.path.expanduser('~/jarvis-app/morning_report.txt')

def log_conversation(user_msg, jarvis_response, model_used, response_time):
    logs = []
    if os.path.exists(LOG_FILE):
        logs = json.load(open(LOG_FILE))
    logs.append({
        'time': datetime.datetime.now().isoformat(),
        'user': user_msg,
        'response': jarvis_response,
        'model': model_used,
        'response_time': response_time
    })
    json.dump(logs, open(LOG_FILE, 'w'), indent=2)

def nightly_improvement():
    print('◈ NIGHTLY IMPROVEMENT CYCLE STARTING...')

    # Read conversation logs
    if not os.path.exists(LOG_FILE):
        print('No logs found, skipping.')
        return
    logs = json.load(open(LOG_FILE))
    if not logs:
        return

    # Build summary for the AI to analyze
    summary = "Here are today's JARVIS conversations:\n\n"
    for log in logs[-20:]:
        summary += f"User: {log['user']}\n"
        summary += f"JARVIS ({log['model']}, {log['response_time']}s): {log['response'][:200]}\n\n"

    # Ask the AI to suggest improvements
    prompt = f"""You are analyzing JARVIS AI assistant logs to suggest code improvements.

{summary}

Based on these conversations, suggest 1-3 specific improvements to make JARVIS better.
Focus on: speed, accuracy, missing features the user needed, repeated questions.
Be specific and brief. Format as a numbered list."""

    try:
        res = requests.post('http://localhost:11434/api/generate', json={
            'model': 'phi3',
            'prompt': prompt,
            'stream': False,
            'keep_alive': -1
        }, timeout=60)
        suggestions = res.json()['response']
    except Exception as e:
        suggestions = f"Could not generate suggestions: {e}"

    # Back up current files
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M')
    shutil.copy('app.py', f'backups/app_{timestamp}.py')
    shutil.copy('index.html', f'backups/index_{timestamp}.html')

    # Write morning report
    report = f"""◈ JARVIS NIGHTLY REPORT — {datetime.datetime.now().strftime('%B %d, %Y')}

CONVERSATIONS TODAY: {len(logs)}
BACKUP SAVED: backups/app_{timestamp}.py

IMPROVEMENT SUGGESTIONS:
{suggestions}

FILES BACKED UP: app_{timestamp}.py, index_{timestamp}.html
"""
    open(REPORT_FILE, 'w').write(report)
    print(report)
    print('✓ NIGHTLY CYCLE COMPLETE')

def run_scheduler():
    os.makedirs(os.path.expanduser('~/jarvis-app/backups'), exist_ok=True)
    schedule.every().day.at("02:00").do(nightly_improvement)
    print('◈ SKYNET SCHEDULER ONLINE — NIGHTLY IMPROVEMENT AT 2AM')
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == '__main__':
    run_scheduler()
