from flask import Flask, request, jsonify, send_from_directory, Response, stream_with_context
import requests
import json
import time
import os
import subprocess

app = Flask(__name__)

ROUTER_PROMPT = """You are a model router. Based on the user message, respond with ONLY one of these exact strings and nothing else:
- phi3 (for casual chat, simple questions, quick tasks)
- llama3.1:8b (for complex reasoning, long answers, analysis)
- qwen2.5-coder:7b (for coding, programming, scripts, technical)
- codellama:7b (for code review, debugging, explaining code)

User message: """

SYSTEM_PROMPT = """You are JARVIS, a highly intelligent personal AI assistant running locally on a MacBook Pro. You are sharp, efficient, and slightly witty like the AI from Iron Man. Keep responses concise and useful.

Only modify your code if the user explicitly says "modify yourself" or "rewrite your code". Otherwise respond normally and concisely."""

def route_model(message):
    try:
        res = requests.post('http://localhost:11434/api/generate', json={
            'model': 'phi3',
            'prompt': ROUTER_PROMPT + message,
            'stream': False,
            'keep_alive': -1
        }, timeout=15)
        model = res.json()['response'].strip().lower()
        valid = ['phi3', 'llama3.1:8b', 'qwen2.5-coder:7b', 'codellama:7b']
        for v in valid:
            if v in model:
                return v
        return 'phi3'
    except:
        return 'phi3'

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/debug')
def debug():
    results = {}
    try:
        start = time.time()
        r = requests.get('http://localhost:11434/api/tags', timeout=5)
        results['ollama_ping'] = f"{round((time.time()-start)*1000)}ms"
        results['models'] = [m['name'] for m in r.json().get('models', [])]
    except Exception as e:
        results['ollama_error'] = str(e)
    try:
        r2 = requests.get('http://localhost:11434/api/ps', timeout=5)
        results['loaded_models'] = r2.json()
    except Exception as e:
        results['ps_error'] = str(e)
    try:
        requests.get('http://localhost:5678', timeout=2)
        results['n8n'] = 'online'
    except:
        results['n8n'] = 'offline'
    return jsonify(results)

@app.route('/read-file', methods=['POST'])
def read_file():
    data = request.json
    filename = data.get('filename', '')
    if filename not in ['app.py', 'index.html']:
        return jsonify({'error': 'unauthorized'})
    try:
        content = open(f'/Users/{os.getenv("USER")}/jarvis-app/{filename}').read()
        return jsonify({'content': content})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/write-file', methods=['POST'])
def write_file():
    data = request.json
    filename = data.get('filename', '')
    content = data.get('content', '')
    if filename not in ['app.py', 'index.html']:
        return jsonify({'error': 'unauthorized'})
    try:
        path = f'/Users/{os.getenv("USER")}/jarvis-app/{filename}'
        open(path, 'w').write(content)
        if filename == 'app.py':
            subprocess.Popen(['python3', 'app.py'], cwd=f'/Users/{os.getenv("USER")}/jarvis-app')
            return jsonify({'status': 'restarting'})
        return jsonify({'status': 'saved'})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message', '')
    manual_model = data.get('model', 'auto')

    # Detect action keywords and route to agent
    action_keywords = ['list', 'open', 'create', 'delete', 'move', 'copy', 'run', 'execute', 'find', 'search files', 'show files', 'organize', 'launch']
    is_action = any(word in message.lower() for word in action_keywords)
    if is_action:
        selected = 'agent'
    else:
        selected = 'llama3.1:8b'

    # Load memory context
    try:
        import memory as mem
        memory_context = mem.get_context()
        mem.load_memory()['last_seen']
        import datetime
        with open(os.path.expanduser('~/jarvis-app/memory.json'), 'r+') as mf:
            mdata = json.load(mf)
            mdata['last_seen'] = datetime.datetime.now().isoformat()
            mf.seek(0)
            json.dump(mdata, mf, indent=2)
    except:
        memory_context = ""

    # Log conversation
    import datetime
    with open(os.path.expanduser('~/jarvis-app/conversations.log'), 'a') as f:
        f.write(f"[{datetime.datetime.now().isoformat()}] USER: {message}\n")

    if selected == 'agent':
        def generate():
            yield "[JARVIS AGENT MODE]\n\nI want to run this on your computer:\n\n" + message + "\n\nClick APPROVE in the UI to execute."
        return Response(stream_with_context(generate()), content_type='text/plain')

    def generate():
        try:
            groq_res = requests.post('https://api.groq.com/openai/v1/chat/completions',
                headers={
                    'Authorization': 'Bearer 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',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': 'llama-3.1-8b-instant',
                    'messages': [
                        {'role': 'system', 'content': SYSTEM_PROMPT + memory_context},
                        {'role': 'user', 'content': message}
                    ],
                    'stream': True,
                    'max_tokens': 1024
                },
                stream=True, timeout=30
            )
            for line in groq_res.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: ') and line != 'data: [DONE]':
                        chunk = json.loads(line[6:])
                        delta = chunk['choices'][0]['delta'].get('content', '')
                        if delta:
                            yield delta
        except Exception as e:
            yield f"\n⚠ ERROR: {str(e)}"

    return Response(stream_with_context(generate()), content_type='text/plain')

@app.route('/status')
def status():
    results = {}
    try:
        requests.get('http://localhost:11434', timeout=2)
        results['ollama'] = 'online'
    except:
        results['ollama'] = 'offline'
    try:
        requests.get('http://localhost:5678', timeout=2)
        results['n8n'] = 'online'
    except:
        results['n8n'] = 'offline'
    return jsonify(results)

@app.route('/agent', methods=['POST'])
def agent():
    data = request.json
    task = data.get('task', '')
    approved = data.get('approved', False)
    if not approved:
        return jsonify({'status': 'pending', 'task': task})
    import subprocess, os, glob
    output = []
    task_lower = task.lower()
    try:
        if 'desktop' in task_lower and ('list' in task_lower or 'show' in task_lower or 'what' in task_lower):
            files = os.listdir(os.path.expanduser('~/Desktop'))
            output.append('Files on your Desktop:\n' + '\n'.join(f'  • {f}' for f in sorted(files)))
        elif 'download' in task_lower and ('list' in task_lower or 'show' in task_lower):
            files = os.listdir(os.path.expanduser('~/Downloads'))
            output.append('Files in Downloads:\n' + '\n'.join(f'  • {f}' for f in sorted(files)))
        elif 'document' in task_lower and ('list' in task_lower or 'show' in task_lower):
            files = os.listdir(os.path.expanduser('~/Documents'))
            output.append('Files in Documents:\n' + '\n'.join(f'  • {f}' for f in sorted(files)))
        elif 'open' in task_lower:
            app = task.split('open')[-1].strip()
            subprocess.Popen(['open', '-a', app])
            output.append(f'Opening {app}...')
        else:
            result = subprocess.run(['python3', '-c', f'import os; print(os.listdir(os.path.expanduser("~")))'],
                capture_output=True, text=True, timeout=10)
            output.append(result.stdout or 'Task completed.')
    except Exception as e:
        return jsonify({{'status': 'error', 'output': '', 'error': str(e)}})
    return jsonify({'status': 'done', 'output': '\n'.join(output), 'error': ''})

if __name__ == '__main__':
    app.run(port=8080, debug=False)
