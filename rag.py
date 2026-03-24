import os
import json

KNOWLEDGE_DIR = os.path.expanduser('~/jarvis-app/knowledge')

def load_knowledge():
    docs = []
    if not os.path.exists(KNOWLEDGE_DIR):
        return ""
    for filename in os.listdir(KNOWLEDGE_DIR):
        filepath = os.path.join(KNOWLEDGE_DIR, filename)
        try:
            with open(filepath, 'r') as f:
                content = f.read()
                docs.append(f"[{filename}]: {content[:500]}")
        except:
            pass
    return '\n'.join(docs) if docs else ""

def get_context():
    knowledge = load_knowledge()
    if not knowledge:
        return ""
    return f"\n\nPERSONAL KNOWLEDGE BASE:\n{knowledge}\n"
