import json
import os
from datetime import datetime

MEMORY_FILE = os.path.expanduser('~/jarvis-app/memory.json')

def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {"facts": [], "preferences": [], "patterns": [], "last_seen": None}
    with open(MEMORY_FILE) as f:
        return json.load(f)

def save_memory(memory):
    with open(MEMORY_FILE, 'w') as f:
        json.dump(memory, f, indent=2)

def add_fact(fact):
    memory = load_memory()
    memory['facts'].append({"fact": fact, "date": datetime.now().isoformat()})
    memory['last_seen'] = datetime.now().isoformat()
    save_memory(memory)

def add_pattern(pattern):
    memory = load_memory()
    memory['patterns'].append({"pattern": pattern, "date": datetime.now().isoformat()})
    save_memory(memory)

def get_context():
    memory = load_memory()
    if not any([memory['facts'], memory['preferences'], memory['patterns']]):
        return ""
    context = "\n\nWHAT YOU KNOW ABOUT THE USER:\n"
    for f in memory['facts'][-10:]:
        context += f"- {f['fact']}\n"
    for p in memory['patterns'][-5:]:
        context += f"- Pattern: {p['pattern']}\n"
    if memory['last_seen']:
        context += f"- Last session: {memory['last_seen']}\n"
    return context

if __name__ == '__main__':
    print(json.dumps(load_memory(), indent=2))
