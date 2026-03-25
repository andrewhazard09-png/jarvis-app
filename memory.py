import json
import os

MEMORY_FILE = os.path.expanduser('~/jarvis-app/memory.json')

def load_memory():
    try:
        with open(MEMORY_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_memory(data):
    with open(MEMORY_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def remember(key, value):
    memory = load_memory()
    memory[key] = value
    save_memory(memory)

def get_context():
    memory = load_memory()
    if not memory:
        return ""
    lines = [f"- {k}: {v}" for k, v in memory.items()]
    return "\nWhat you know about Drew:\n" + "\n".join(lines)
