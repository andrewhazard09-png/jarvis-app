import requests
import json
import os
import shutil
from datetime import datetime

LOG_FILE = os.path.expanduser('~/jarvis-app/conversations.log')
BACKUP_DIR = os.path.expanduser('~/jarvis-app/backups')

def backup_files():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    shutil.copy(os.path.expanduser('~/jarvis-app/app.py'), f'{BACKUP_DIR}/app_{timestamp}.py')
    shutil.copy(os.path.expanduser('~/jarvis-app/index.html'), f'{BACKUP_DIR}/index_{timestamp}.html')
    print(f'✓ Backed up to {BACKUP_DIR}')

def get_recent_logs():
    if not os.path.exists(LOG_FILE):
        return "No conversations logged yet."
    with open(LOG_FILE) as f:
        lines = f.readlines()
    return ''.join(lines[-50:])

def ask_ollama(prompt):
    res = requests.post('https://api.groq.com/openai/v1/chat/completions',
        headers={
            'Authorization': 'Bearer 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',
            'Content-Type': 'application/json'
        },
        json={
            'model': 'llama-3.1-8b-instant',
            'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': 200
        },
        timeout=30
    )
    return res.json()['choices'][0]['message']['content']

def run_improvement():
    print('◈ JARVIS SELF-IMPROVEMENT STARTING...')
    backup_files()
    
    logs = get_recent_logs()
    current_code = open(os.path.expanduser('~/jarvis-app/app.py')).read()
    
    analysis = ask_ollama(f"""You are analyzing JARVIS AI assistant logs to find improvements.
    
Recent conversations:
{logs}

Current app.py code summary:
- Flask app on port 8080
- Routes: /chat, /agent, /status, /debug, /read-file, /write-file
- Uses phi3 model via Ollama

Based on the conversations, suggest ONE specific small improvement in plain English.
Keep it under 50 words. Focus on making responses faster or more accurate.""")
    
    print(f'◈ IMPROVEMENT IDENTIFIED: {analysis}')
    
    report = {
        'date': datetime.now().isoformat(),
        'improvement': analysis,
        'status': 'analyzed'
    }
    
    with open(os.path.expanduser('~/jarvis-app/improvement_log.json'), 'a') as f:
        f.write(json.dumps(report) + '\n')
    
    print('✓ IMPROVEMENT CYCLE COMPLETE')
    print(f'✓ Report saved to ~/jarvis-app/improvement_log.json')

if __name__ == '__main__':
    run_improvement()
