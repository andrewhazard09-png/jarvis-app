from flask import Flask, request, jsonify, send_from_directory, Response, stream_with_context
from config import GROQ_KEY, OPENROUTER_KEY, WEATHER_KEY, NEWS_KEY
from bs4 import BeautifulSoup
import requests
import json
import time
import os
import subprocess
import datetime

from mac_bridge import handle_mac_command  # <-- All Mac commands handled here

app = Flask(__name__)

# -------------------- Utilities --------------------

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
        res = requests.get(
            f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_KEY}&units=imperial',
            timeout=10
        )
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
        res = requests.get(
            f'https://newsapi.org/v2/everything?q={topic}&sortBy=publishedAt&pageSize=3&apiKey={NEWS_KEY}',
            timeout=10
        )
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
- Only modify your code if Drew explicitly says "modify yourself"
- You are always talking directly to Drew"""

# -------------------- Flask Routes --------------------

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

# -------------------- Chat Endpoint --------------------

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message', '')
    mac_result = handle_mac_command(message)
    if mac_result is not None:
        print("\n--- REQUEST ---")
        print("USER:", message)
        print("MAC:", mac_result)
        def generate():
            yield mac_result
        return Response(stream_with_context(generate()), content_type='text/plain')
    msg = message.lower()

    print("\n--- REQUEST ---")
    print("USER:", message)

    # WEATHER CHECK
    if "weather" in msg:
        result = get_weather("Nyack")
        print("WEATHER:", result)
        return result

    # AI FALLBACK
    try:
        res = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": message}
                ]
            }
        )
        reply = res.json()["choices"][0]["message"]["content"]
        print("AI:", reply)
        return reply
    except Exception as e:
        print("AI ERROR:", e)
        return "Error talking to AI."

# -------------------- Feedback / History --------------------

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

# -------------------- Agent Tasks --------------------

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

# -------------------- Main --------------------

if __name__ == '__main__':
    app.run(port=8080, debug=True)
