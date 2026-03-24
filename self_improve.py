import threading
import time
import requests
import json
import os
import shutil
from datetime import datetime

try:
    from config import GROQ_KEY, OPENROUTER_KEY, NEWS_KEY
except:
    GROQ_KEY = None
    OPENROUTER_KEY = None
    NEWS_KEY = None

LOG_FILE = os.path.expanduser('~/jarvis-app/self_improve.log')
CONV_LOG = os.path.expanduser('~/jarvis-app/conversations.log')
FEEDBACK_LOG = os.path.expanduser('~/jarvis-app/feedback.log')
SCORES_FILE = os.path.expanduser('~/jarvis-app/scores.json')
MEMORY_FILE = os.path.expanduser('~/jarvis-app/memory.json')
KNOWLEDGE_DIR = os.path.expanduser('~/jarvis-app/knowledge')
BACKUP_DIR = os.path.expanduser('~/jarvis-app/backups')
APP_PATH = os.path.expanduser('~/jarvis-app/app.py')

def log(msg):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_FILE, 'a') as f:
        f.write(f'[{timestamp}] {msg}\n')
    print(f'[SELF-IMPROVE] {msg}')

def ask_groq(prompt, max_tokens=512, model='llama-3.1-8b-instant'):
    if not GROQ_KEY:
        return None
    try:
        res = requests.post('https://api.groq.com/openai/v1/chat/completions',
            headers={'Authorization': f'Bearer {GROQ_KEY}', 'Content-Type': 'application/json'},
            json={
                'model': model,
                'messages': [{'role': 'user', 'content': prompt}],
                'max_tokens': max_tokens
            },
            timeout=30
        )
        return res.json()['choices'][0]['message']['content']
    except Exception as e:
        log(f'Groq error: {str(e)}')
        return None

def get_recent_convos():
    if not os.path.exists(CONV_LOG):
        return ""
    with open(CONV_LOG) as f:
        lines = f.readlines()
    return ''.join(lines[-30:])

# Feature 1: Learn topics and save to memory
def learn_topics():
    try:
        convos = get_recent_convos()
        if not convos:
            return
        topics = ask_groq(f"""From these conversations extract the top 3 topics the user asks about most.
Respond with ONLY a JSON array like: ["sports", "news", "weather"]
Conversations: {convos}""", max_tokens=100)
        if not topics or not topics.strip().startswith('['):
            return
        memory = {}
        if os.path.exists(MEMORY_FILE):
            memory = json.load(open(MEMORY_FILE))
        memory['top_topics'] = json.loads(topics.strip())
        memory['last_updated'] = datetime.now().isoformat()
        json.dump(memory, open(MEMORY_FILE, 'w'), indent=2)
        log(f'Learned topics: {topics.strip()}')
    except Exception as e:
        log(f'Topic learning failed: {str(e)}')

# Feature 2: Analyze feedback and identify weak spots
def analyze_feedback():
    try:
        if not os.path.exists(FEEDBACK_LOG):
            return
        lines = open(FEEDBACK_LOG).readlines()
        if len(lines) < 3:
            return
        bad = []
        for line in lines[-20:]:
            try:
                entry = json.loads(line.strip())
                if entry.get('rating') == 0:
                    bad.append(entry.get('message', ''))
            except:
                pass
        if not bad:
            log('Feedback analysis: no bad ratings recently, all good.')
            return
        analysis = ask_groq(f"""These are messages where the AI gave bad responses: {bad}
In one sentence, what is the common pattern or weakness? Be specific.""", max_tokens=100)
        if analysis:
            log(f'Feedback weakness identified: {analysis.strip()}')
            memory = {}
            if os.path.exists(MEMORY_FILE):
                memory = json.load(open(MEMORY_FILE))
            memory['known_weakness'] = analysis.strip()
            json.dump(memory, open(MEMORY_FILE, 'w'), indent=2)
    except Exception as e:
        log(f'Feedback analysis failed: {str(e)}')

# Feature 3: Auto build knowledge base from top topics
def build_knowledge():
    try:
        os.makedirs(KNOWLEDGE_DIR, exist_ok=True)
        if not os.path.exists(MEMORY_FILE):
            return
        memory = json.load(open(MEMORY_FILE))
        topics = memory.get('top_topics', [])
        if not topics:
            return
        for topic in topics[:2]:
            filename = os.path.join(KNOWLEDGE_DIR, f'{topic.replace(" ", "_")}.txt')
            # Only update if file is older than 24 hours or doesn't exist
            if os.path.exists(filename):
                age = time.time() - os.path.getmtime(filename)
                if age < 86400:
                    continue
            summary = ask_groq(f"""Write a 3-5 sentence factual summary of current knowledge about: {topic}
This will be used as context for an AI assistant. Be factual and concise.""", max_tokens=200)
            if summary:
                open(filename, 'w').write(f"Topic: {topic}\nLast updated: {datetime.now().isoformat()}\n\n{summary}")
                log(f'Built knowledge file for: {topic}')
    except Exception as e:
        log(f'Knowledge building failed: {str(e)}')

# Feature 4: Check for better models on Groq
def check_better_models():
    try:
        res = requests.get('https://api.groq.com/openai/v1/models',
            headers={'Authorization': f'Bearer {GROQ_KEY}'}, timeout=10)
        models = [m['id'] for m in res.json().get('data', [])]
        preferred = ['llama-3.3-70b-versatile', 'llama-3.1-70b-versatile', 'llama-3.1-8b-instant']
        best = next((p for p in preferred if p in models), None)
        if not best:
            return
        current = open(APP_PATH).read()
        if best in current:
            log(f'Already using best model: {best}')
            return
        log(f'Better model found: {best} — updating...')
        temp = APP_PATH + '.tmp'
        new_code = current.replace('llama-3.1-8b-instant', best).replace('llama-3.1-70b-versatile', best)
        open(temp, 'w').write(new_code)
        import subprocess
        result = subprocess.run(['python3', '-m', 'py_compile', temp], capture_output=True)
        if result.returncode == 0:
            os.makedirs(BACKUP_DIR, exist_ok=True)
            shutil.copy(APP_PATH, f'{BACKUP_DIR}/app_{datetime.now().strftime("%Y%m%d_%H%M%S")}.py')
            shutil.copy(temp, APP_PATH)
            os.remove(temp)
            log(f'Upgraded to model: {best}')
        else:
            os.remove(temp)
            log('Model upgrade syntax check failed')
    except Exception as e:
        log(f'Model check failed: {str(e)}')

# Feature 5: Check for better free models on OpenRouter
def check_openrouter_models():
    try:
        res = requests.get('https://openrouter.ai/api/v1/models',
            headers={'Authorization': f'Bearer {OPENROUTER_KEY}'}, timeout=10)
        models = res.json().get('data', [])
        free_models = [m['id'] for m in models if ':free' in m['id']]
        # Look for large capable free models
        preferred_free = [m for m in free_models if any(x in m for x in ['70b', '72b', '90b', '405b'])]
        if not preferred_free:
            return
        best_free = preferred_free[0]
        current = open(APP_PATH).read()
        if best_free in current:
            log(f'OpenRouter already using good free model: {best_free}')
            return
        log(f'Better OpenRouter free model found: {best_free}')
        memory = {}
        if os.path.exists(MEMORY_FILE):
            memory = json.load(open(MEMORY_FILE))
        memory['best_openrouter_model'] = best_free
        json.dump(memory, open(MEMORY_FILE, 'w'), indent=2)
        log(f'Saved best OpenRouter model to memory: {best_free}')
    except Exception as e:
        log(f'OpenRouter model check failed: {str(e)}')

# Feature 6: Score recent conversation quality
def score_conversations():
    try:
        convos = get_recent_convos()
        if not convos:
            return
        score = ask_groq(f"""Rate the quality of these AI responses from 1-10.
Consider: accuracy, helpfulness, naturalness, not making stuff up.
Respond with ONLY a single number 1-10.
Conversations: {convos[-500:]}""", max_tokens=10)
        if score:
            try:
                score_val = int(score.strip())
                scores = {}
                if os.path.exists(SCORES_FILE):
                    scores = json.load(open(SCORES_FILE))
                scores[datetime.now().isoformat()] = score_val
                # Keep last 100
                if len(scores) > 100:
                    oldest = sorted(scores.keys())[0]
                    del scores[oldest]
                json.dump(scores, open(SCORES_FILE, 'w'), indent=2)
                log(f'Conversation quality score: {score_val}/10')
            except:
                pass
    except Exception as e:
        log(f'Scoring failed: {str(e)}')

def run_all():
    log('Self improvement system v2 started.')
    cycle = 0
    while True:
        time.sleep(600)
        cycle += 1
        log(f'--- Cycle #{cycle} starting ---')
        try:
            learn_topics()
        except:
            pass
        try:
            analyze_feedback()
        except:
            pass
        try:
            score_conversations()
        except:
            pass
        try:
            build_knowledge()
        except:
            pass
        if cycle % 6 == 0:
            try:
                check_better_models()
            except:
                pass
            try:
                check_openrouter_models()
            except:
                pass
        log(f'--- Cycle #{cycle} complete ---')

def start():
    t = threading.Thread(target=run_all, daemon=True)
    t.start()
    log('Self improvement v2 thread launched.')
