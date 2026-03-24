import requests
from bs4 import BeautifulSoup
import json
import os
import subprocess
import shutil
from datetime import datetime

BACKUP_DIR = os.path.expanduser('~/jarvis-app/backups')
LOG_FILE = os.path.expanduser('~/jarvis-app/research_log.json')

SEARCH_QUERIES = [
    "best local AI assistant features 2026",
    "ollama jarvis setup new features",
    "open webui new features 2026",
    "local LLM voice assistant setup"
]

def backup():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    shutil.copy(os.path.expanduser('~/jarvis-app/app.py'), f'{BACKUP_DIR}/app_{timestamp}.py')
    shutil.copy(os.path.expanduser('~/jarvis-app/index.html'), f'{BACKUP_DIR}/index_{timestamp}.html')
    print(f'✓ Backed up')

def search_web(query):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
        url = f'https://html.duckduckgo.com/html/?q={query.replace(" ", "+")}'
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        results = []
        for r in soup.find_all('a', class_='result__snippet')[:5]:
            text = r.get_text()
            if len(text) > 50:
                results.append(text)
        return results
    except Exception as e:
        return [str(e)]

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

def check_syntax(filepath):
    result = subprocess.run(
        ['python3', '-m', 'py_compile', filepath],
        capture_output=True, text=True
    )
    return result.returncode == 0

def research_and_improve():
    print('◈ JARVIS RESEARCHER STARTING...')
    backup()

    # Search for new features
    all_findings = []
    for query in SEARCH_QUERIES:
        print(f'◈ SEARCHING: {query}')
        results = search_web(query)
        all_findings.extend(results)

    findings_text = '\n'.join(all_findings[:10])
    print(f'◈ FOUND {len(all_findings)} RESULTS')

    # Ask ollama what to add
    current_code = open(os.path.expanduser('~/jarvis-app/app.py')).read()
    
    short_findings = ' '.join(all_findings[:3])[:500]
    suggestion = ask_ollama(f"""Based on this AI news: {short_findings}
    
Suggest ONE feature to add to a local AI chat app. Under 20 words. Plain English only.""")

    print(f'◈ IMPROVEMENT IDENTIFIED: {suggestion}')

    # Log the research
    log = {
        'date': datetime.now().isoformat(),
        'findings': all_findings[:5],
        'suggestion': suggestion,
        'status': 'researched'
    }

    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps(log) + '\n')

    print('✓ RESEARCH COMPLETE')
    print(f'✓ Check ~/jarvis-app/research_log.json for results')

if __name__ == '__main__':
    research_and_improve()
