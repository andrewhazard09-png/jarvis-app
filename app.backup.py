from flask import Flask, request, jsonify, send_from_directory, Response, stream_with_context
from config import GROQ_KEY, OPENROUTER_KEY, WEATHER_KEY, NEWS_KEY
from bs4 import BeautifulSoup
import requests
import json
import time
import os
import subprocess
import datetime

app = Flask(__name__)

# Start live screen capture
try:
    import screen_reader
    screen_reader.start_live_capture()
except:
    pass

# Start self improvement system
try:
    import self_improve
    self_improve.start()
except:
    pass

def web_search(query):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
        url = 'https://html.duckduckgo.com/html/?q=' + query.replace(' ', '+')
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        results = []
        for r in soup.find_all('a', class_='result__snippet')[:5]:
            text = r.get_text().strip()
            if len(text) > 30:
                results.append(text)
        if not results:
            return 'No results found.'
        return ' | '.join(results[:5])
    except Exception as e:
        return 'Search unavailable: ' + str(e)

def get_weather(city="Nyack"):
    try:
        res = requests.get(f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_KEY}&units=imperial', timeout=10)
        data = res.json()
        temp = data['main']['temp']
        feels = data['main']['feels_like']
        desc = data['weather'][0]['description']
        humidity = data['main']['humidity']
        return f"Weather in {city}: {desc}, {temp}°F (feels like {feels}°F), humidity {humidity}%"
    except Exception as e:
        return f"Weather unavailable: {str(e)}"

def get_news(topic="world"):
    try:
        res = requests.get(f'https://newsapi.org/v2/everything?q={topic}&sortBy=publishedAt&pageSize=3&apiKey={NEWS_KEY}', timeout=10)
        articles = res.json().get('articles', [])
        if not articles:
            return "No news found."
        result = f"Latest {topic} news:\n"
        for a in articles[:3]:
            result += f"• {a['title']} — {a['source']['name']}\n"
        return result
    except Exception as e:
        return f"News unavailable: {str(e)}"

def morning_summary():
    weather = get_weather("Nyack")
    news = get_news("world")
    try:
        import sports
        scores = sports.get_scores('nba')
    except:
        scores = "Sports scores unavailable."
    return f"Good morning, Drew.\n\n{weather}\n\n{news}\n\n{scores}"

SYSTEM_PROMPT = """You are JARVIS, a highly intelligent personal AI assistant running on Drew's MacBook Pro. You are sharp, efficient, and slightly witty like the AI from Iron Man.

Facts about yourself:
- Built by Drew, you run locally on his Mac
- You can control his Mac, search the web, check news and weather, and see his screen
- You remember this conversation and learn over time
- When Drew asks what you can do, list your actual capabilities
- For casual conversation respond naturally, never search the web for personal statements
- If Drew says something personal like "I went to a parade", respond conversationally
- Only modify your code if Drew explicitly says "modify yourself"
- You are always talking directly to Drew"""

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
        requests.get('http://localhost:5678', timeout=2)
        results['n8n'] = 'online'
    except:
        results['n8n'] = 'offline'
    results['groq'] = 'configured'
    results['openrouter'] = 'configured'
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
    history = data.get('history', [])

    msg_lower = message.lower()

    # Load RAG knowledge
    try:
        import rag
        knowledge_context = rag.get_context()
    except:
        knowledge_context = ""

    # Load memory context
    try:
        import memory as mem
        memory_context = mem.get_context() + knowledge_context
        with open(os.path.expanduser('~/jarvis-app/memory.json'), 'r+') as mf:
            mdata = json.load(mf)
            mdata['last_seen'] = datetime.datetime.now().isoformat()
            mf.seek(0)
            json.dump(mdata, mf, indent=2)
    except:
        memory_context = knowledge_context

    # Log conversation
    with open(os.path.expanduser('~/jarvis-app/conversations.log'), 'a') as f:
        f.write(f"[{datetime.datetime.now().isoformat()}] USER: {message}\n")

    # Good morning summary
    if 'good morning' in msg_lower:
        result = morning_summary()
        def generate():
            yield result
        return Response(stream_with_context(generate()), content_type='text/plain')

    # Self coding
    if any(t in msg_lower for t in ['add a feature', 'add feature', 'modify yourself', 'update yourself', 'change yourself']):
        try:
            import self_coder
            result = self_coder.propose_change(message)
            def generate():
                yield result['message']
            return Response(stream_with_context(generate()), content_type='text/plain')
        except Exception as e:
            pass

    if any(t in msg_lower for t in ['apply the change', 'apply change', 'confirm the change', 'yes apply']):
        try:
            import self_coder
            result = self_coder.apply_change()
            def generate():
                yield result['message']
            return Response(stream_with_context(generate()), content_type='text/plain')
        except Exception as e:
            pass

    if any(t in msg_lower for t in ['cancel the change', 'cancel change', 'discard the change']):
        try:
            import self_coder
            result = self_coder.cancel_change()
            def generate():
                yield result['message']
            return Response(stream_with_context(generate()), content_type='text/plain')
        except Exception as e:
            pass

    # Screen reading
    screen_triggers = ['look at my screen', 'what do you see', 'whats on my screen', 'read my screen', 'what am i looking at']
    if any(t in msg_lower for t in screen_triggers):
        try:
            import screen_reader
            result = screen_reader.read_screen(message)
            def generate():
                yield result
            return Response(stream_with_context(generate()), content_type='text/plain')
        except:
            pass

    # Weather
    if any(w in msg_lower for w in ['weather', 'temperature', 'forecast']):
        result = get_weather("Nyack")
        def generate():
            yield result
        return Response(stream_with_context(generate()), content_type='text/plain')

    # News
    if any(w in msg_lower for w in ['whats the news', 'what is the news', 'latest news', 'top headlines']):
        skip = {'news','headlines','latest','what','is','the','about','whats','happening','on','in','a','an','tell','me','give','get','recent','today','big','top','any','that','are','important','some','current','new'}
        words = [w for w in msg_lower.split() if w not in skip]
        topic = ' '.join(words) if words else 'world'
        result = get_news(topic)
        def generate():
            yield result
        return Response(stream_with_context(generate()), content_type='text/plain')

    # Mac bridge for app control
    try:
        import mac_bridge
        mac_result = mac_bridge.handle_mac_command(message)
        if mac_result:
            def generate():
                yield mac_result
            return Response(stream_with_context(generate()), content_type='text/plain')
    except:
        pass

    # Sports scores - direct requests only
    direct_score_triggers = ['what are the scores', 'todays scores', 'last nights scores', 'nba scores', 'nfl scores', 'mlb scores', 'nhl scores']
    if any(t in msg_lower for t in direct_score_triggers):
        try:
            import sports
            sport = sports.detect_sport(message)
            result = sports.get_scores(sport)
            def generate():
                yield result
            return Response(stream_with_context(generate()), content_type='text/plain')
        except Exception as e:
            pass

    # Smart search detection
    def needs_current_info(msg):
        try:
            res = requests.post('https://api.groq.com/openai/v1/chat/completions',
                headers={'Authorization': 'Bearer ' + GROQ_KEY, 'Content-Type': 'application/json'},
                json={
                    'model': 'llama-3.1-8b-instant',
                    'messages': [{'role': 'user', 'content': f'Does answering this require current real-time information that could have changed in the last week? Answer ONLY yes or no. Question: {msg}'}],
                    'max_tokens': 5
                },
                timeout=10
            )
            answer = res.json()['choices'][0]['message']['content'].strip().lower()
            return 'yes' in answer
        except:
            return False

    if needs_current_info(message):
        search_results = web_search(message)
        def generate():
            prompt = 'Based on these real search results, answer concisely: ' + message + '\nResults: ' + search_results + '\nNever make up data not in the results.'
            groq_res = requests.post('https://api.groq.com/openai/v1/chat/completions',
                headers={'Authorization': 'Bearer ' + GROQ_KEY, 'Content-Type': 'application/json'},
                json={
                    'model': 'llama-3.3-70b-versatile',
                    'messages': [{'role': 'system', 'content': SYSTEM_PROMPT}] + history[-6:] + [{'role': 'user', 'content': prompt}],
                    'stream': True,
                    'max_tokens': 512
                },
                stream=True, timeout=30)
            for line in groq_res.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: ') and line != 'data: [DONE]':
                        chunk = json.loads(line[6:])
                        delta = chunk['choices'][0]['delta'].get('content', '')
                        if delta:
                            yield delta
        return Response(stream_with_context(generate()), content_type='text/plain')

    # Agent mode
    agent_triggers = ['list my files', 'show my files', 'open the app', 'delete this file', 'organize my desktop']
    if any(t in msg_lower for t in agent_triggers):
        def generate():
            yield "[JARVIS AGENT MODE]\n\nI want to run this on your computer:\n\n" + message + "\n\nClick APPROVE in the UI to execute."
        return Response(stream_with_context(generate()), content_type='text/plain')

    # Main chat via Groq with OpenRouter fallback
    def generate():
        try:
            groq_res = requests.post('https://api.groq.com/openai/v1/chat/completions',
                headers={'Authorization': 'Bearer ' + GROQ_KEY, 'Content-Type': 'application/json'},
                json={
                    'model': 'llama-3.3-70b-versatile',
                    'messages': [
                        {'role': 'system', 'content': SYSTEM_PROMPT + memory_context}
                    ] + history[-6:] + [
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
            try:
                or_res = requests.post('https://openrouter.ai/api/v1/chat/completions',
                    headers={'Authorization': 'Bearer ' + OPENROUTER_KEY, 'Content-Type': 'application/json'},
                    json={
                        'model': 'meta-llama/llama-3.3-70b-instruct',
                        'messages': [
                            {'role': 'system', 'content': SYSTEM_PROMPT + memory_context}
                        ] + history[-6:] + [
                            {'role': 'user', 'content': message}
                        ],
                        'stream': True,
                        'max_tokens': 1024
                    },
                    stream=True, timeout=30
                )
                for line in or_res.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data: ') and line != 'data: [DONE]':
                            chunk = json.loads(line[6:])
                            delta = chunk['choices'][0]['delta'].get('content', '')
                            if delta:
                                yield delta
            except Exception as e2:
                yield f"⚠ All AI services unavailable: {str(e2)}"

    return Response(stream_with_context(generate()), content_type='text/plain')

@app.route('/feedback', methods=['POST'])
def feedback():
    data = request.json
    rating = data.get('rating', 0)
    message = data.get('message', '')
    try:
        with open(os.path.expanduser('~/jarvis-app/feedback.log'), 'a') as f:
            f.write(json.dumps({'rating': rating, 'message': message[:100], 'date': datetime.datetime.now().isoformat()}) + '\n')
    except:
        pass
    return jsonify({'status': 'ok'})

@app.route('/save-history', methods=['POST'])
def save_history():
    data = request.json
    history = data.get('history', [])
    try:
        json.dump(history, open(os.path.expanduser('~/jarvis-app/chat_history.json'), 'w'), indent=2)
    except:
        pass
    return jsonify({'status': 'ok'})

@app.route('/load-history')
def load_history():
    try:
        history = json.load(open(os.path.expanduser('~/jarvis-app/chat_history.json')))
        return jsonify({'history': history[-20:]})
    except:
        return jsonify({'history': []})

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
    output = []
    task_lower = task.lower()
    try:
        if 'desktop' in task_lower and any(w in task_lower for w in ['list', 'show', 'what']):
            files = os.listdir(os.path.expanduser('~/Desktop'))
            output.append('Files on your Desktop:\n' + '\n'.join(f'  • {f}' for f in sorted(files)))
        elif 'download' in task_lower and any(w in task_lower for w in ['list', 'show']):
            files = os.listdir(os.path.expanduser('~/Downloads'))
            output.append('Files in Downloads:\n' + '\n'.join(f'  • {f}' for f in sorted(files)))
        elif 'document' in task_lower and any(w in task_lower for w in ['list', 'show']):
            files = os.listdir(os.path.expanduser('~/Documents'))
            output.append('Files in Documents:\n' + '\n'.join(f'  • {f}' for f in sorted(files)))
        elif 'open' in task_lower:
            app_name = task.split('open')[-1].strip()
            subprocess.Popen(['open', '-a', app_name])
            output.append(f'Opening {app_name}...')
        else:
            output.append('Task received. Try asking me to list files or open an app.')
    except Exception as e:
        return jsonify({'status': 'error', 'output': '', 'error': str(e)})
    return jsonify({'status': 'done', 'output': '\n'.join(output), 'error': ''})

if __name__ == '__main__':
    app.run(port=8080, debug=False)
