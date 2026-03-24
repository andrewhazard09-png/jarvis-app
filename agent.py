import subprocess
import json
import sys
import os

def run_task(task, approved=False):
    if not approved:
        return {"status": "pending", "task": task, "message": "Awaiting your approval"}
    
    result = subprocess.run(
        ['interpreter', '--model', 'ollama/phi3', '--no-highlight', '-y', '--single_output', task],
        capture_output=True, text=True, timeout=60,
        cwd=os.path.expanduser('~')
    )
    return {
        "status": "done",
        "output": result.stdout,
        "error": result.stderr
    }

if __name__ == '__main__':
    task = sys.argv[1] if len(sys.argv) > 1 else "list files on Desktop"
    print(json.dumps(run_task(task, approved=True)))
