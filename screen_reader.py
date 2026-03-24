import subprocess
import os
import base64
import requests
from datetime import datetime

try:
    from config import GROQ_KEY, OPENROUTER_KEY
except:
    GROQ_KEY = None
    OPENROUTER_KEY = None

SCREENSHOT_PATH = os.path.expanduser('~/jarvis-app/screen_capture.png')

def take_screenshot():
    try:
        subprocess.run(['screencapture', '-x', SCREENSHOT_PATH], timeout=5)
        return True
    except:
        return False

def encode_image():
    try:
        with open(SCREENSHOT_PATH, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    except:
        return None

def start_live_capture():
    import threading
    def capture_loop():
        while True:
            try:
                subprocess.run(['screencapture', '-x', SCREENSHOT_PATH], timeout=5)
            except:
                pass
            import time
            time.sleep(2)
    t = threading.Thread(target=capture_loop, daemon=True)
    t.start()

def read_screen(question="What do you see on this screen?"):
    try:
        if not take_screenshot():
            return "Could not take screenshot."
        
        image_data = encode_image()
        if not image_data:
            return "Could not read screenshot."

        # Use OpenRouter free vision model
        res = requests.post('https://openrouter.ai/api/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {OPENROUTER_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'nvidia/nemotron-nano-12b-v2-vl:free',
                'messages': [{
                    'role': 'user',
                    'content': [
                        {
                            'type': 'image_url',
                            'image_url': {
                                'url': f'data:image/png;base64,{image_data}'
                            }
                        },
                        {
                            'type': 'text',
                            'text': f'You are JARVIS analyzing the user screen. {question} Be concise and helpful.'
                        }
                    ]
                }],
                'max_tokens': 512
            },
            timeout=30
        )
        result = res.json()['choices'][0]['message']
        if result.get('content'):
            return result['content']
        elif result.get('reasoning'):
            # Trim reasoning to first 200 chars
            return result['reasoning'][:300].split('.')[0] + '.'
        else:
            return 'Could not read screen.'
    except Exception as e:
        return f"Screen read error: {str(e)}"

if __name__ == '__main__':
    print(read_screen())
