import requests
import subprocess
import shutil
import os
import datetime

try:
    from config import GROQ_KEY
except:
    GROQ_KEY = None

BACKUP_DIR = os.path.expanduser('~/jarvis-app/backups')
APP_PATH = os.path.expanduser('~/jarvis-app/app.py')
PENDING_PATH = os.path.expanduser('~/jarvis-app/app_pending.py')
LOG_PATH = os.path.expanduser('~/jarvis-app/self_coder.log')

def log(msg):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_PATH, 'a') as f:
        f.write(f'[{timestamp}] {msg}\n')

def backup():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    dst = f'{BACKUP_DIR}/app_{timestamp}.py'
    shutil.copy(APP_PATH, dst)
    return dst

def syntax_check(path):
    result = subprocess.run(
        ['python3', '-m', 'py_compile', path],
        capture_output=True, text=True
    )
    return result.returncode == 0

def generate_code(request, current_code):
    if not GROQ_KEY:
        return None
    try:
        prompt = f"""You are modifying a Flask Python app called JARVIS.
Current app.py (relevant sections):
{current_code[:3000]}

Task: {request}

Rules:
- Return ONLY a small Python code snippet to add or change, nothing else
- Maximum 30 lines of code
- Must be valid Python
- Do not rewrite the whole file
- Do not include markdown or explanations
- If the task is too complex or risky, respond with exactly: TOO_COMPLEX

Code change:"""

        res = requests.post('https://api.groq.com/openai/v1/chat/completions',
            headers={'Authorization': f'Bearer {GROQ_KEY}', 'Content-Type': 'application/json'},
            json={
                'model': 'llama-3.1-8b-instant',
                'messages': [{'role': 'user', 'content': prompt}],
                'max_tokens': 400
            },
            timeout=30
        )
        return res.json()['choices'][0]['message']['content'].strip()
    except Exception as e:
        log(f'Code generation failed: {str(e)}')
        return None

def propose_change(request):
    try:
        current_code = open(APP_PATH).read()
        log(f'Received request: {request}')

        code = generate_code(request, current_code)

        if not code or 'TOO_COMPLEX' in code:
            log('Request too complex or generation failed')
            return {'status': 'too_complex', 'message': 'This change is too complex for me to do safely on my own. Ask Claude to help with this one.'}

        # Strip markdown if model added it anyway
        if '```' in code:
            lines = code.split('\n')
            lines = [l for l in lines if not l.startswith('```')]
            code = '\n'.join(lines)

        log(f'Generated code: {code[:100]}')

        # Write to pending file
        new_code = current_code + f'\n\n# AUTO-CHANGE [{datetime.datetime.now().isoformat()}]\n# Request: {request}\n{code}\n'
        open(PENDING_PATH, 'w').write(new_code)

        # Syntax check
        if not syntax_check(PENDING_PATH):
            os.remove(PENDING_PATH)
            log('Syntax check failed — discarded')
            return {'status': 'syntax_error', 'message': 'I tried but the code I generated had errors. Try asking Claude for this one.'}

        log('Syntax check passed — awaiting approval')
        return {
            'status': 'pending_approval',
            'message': f'I can make this change. Here\'s what I\'ll add:\n\n{code}\n\nSay "JARVIS apply the change" to confirm or "JARVIS cancel the change" to discard.',
            'code': code
        }
    except Exception as e:
        log(f'propose_change failed: {str(e)}')
        return {'status': 'error', 'message': f'Something went wrong: {str(e)}'}

def apply_change():
    try:
        if not os.path.exists(PENDING_PATH):
            return {'status': 'error', 'message': 'No pending change to apply.'}

        backup_path = backup()
        log(f'Backed up to {backup_path}')

        shutil.copy(PENDING_PATH, APP_PATH)
        os.remove(PENDING_PATH)
        log('Change applied successfully')
        return {'status': 'applied', 'message': 'Done. Change applied and JARVIS is restarting.'}
    except Exception as e:
        log(f'apply_change failed: {str(e)}')
        return {'status': 'error', 'message': str(e)}

def cancel_change():
    try:
        if os.path.exists(PENDING_PATH):
            os.remove(PENDING_PATH)
        log('Change cancelled')
        return {'status': 'cancelled', 'message': 'Change discarded. Nothing was modified.'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}
