import subprocess
import os

def run_applescript(script):
    try:
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True, text=True, timeout=10
        )
        return result.stdout.strip() or 'Done.'
    except Exception as e:
        return f'Error: {str(e)}'

def handle_mac_command(message):
    msg = message.lower().strip()

    if 'volume up' in msg:
        return run_applescript(
            'set v to (output volume of (get volume settings)) + 10\n'
            'if v > 100 then set v to 100\n'
            'set volume output volume v'
        )
    if 'volume down' in msg:
        return run_applescript(
            'set v to (output volume of (get volume settings)) - 10\n'
            'if v < 0 then set v to 0\n'
            'set volume output volume v'
        )
    if 'max volume' in msg:
        return run_applescript('set volume output volume 100')
    if 'unmute' in msg:
        return run_applescript('set volume output muted false')
    if 'mute' in msg:
        return run_applescript('set volume output muted true')

    if 'battery' in msg:
        try:
            result = subprocess.run(['pmset', '-g', 'batt'], capture_output=True, text=True)
            lines = result.stdout.strip().split('\n')
            return lines[1].strip() if len(lines) > 1 else 'Battery info unavailable'
        except Exception as e:
            return f'Battery error: {str(e)}'

    if 'screenshot' in msg:
        try:
            path = os.path.expanduser('~/Desktop/jarvis_screenshot.png')
            subprocess.run(['screencapture', '-x', path])
            return 'Screenshot saved to Desktop as jarvis_screenshot.png'
        except Exception as e:
            return f'Screenshot error: {str(e)}'

    if 'create note' in msg or 'take note' in msg or 'remind me' in msg:
        try:
            note_text = msg
            for k in ['create note', 'take note', 'remind me']:
                note_text = note_text.replace(k, '').strip()
            note_text = note_text.replace('"', '\\"')
            script = f'tell application "Notes" to make new note with properties {{body:"{note_text}"}}'
            run_applescript(script)
            return f'Note saved: {note_text}'
        except Exception as e:
            return f'Notes error: {str(e)}'

    if 'play' in msg and any(k in msg for k in ['music', 'spotify', 'song']):
        return run_applescript('tell application "Spotify" to play')
    if 'pause' in msg and any(k in msg for k in ['music', 'spotify']):
        return run_applescript('tell application "Spotify" to pause')
    if 'next' in msg and any(k in msg for k in ['song', 'track']):
        return run_applescript('tell application "Spotify" to next track')

    if 'open' in msg or 'launch' in msg:
        app_name = msg.replace('open', '').replace('launch', '').strip().title()
        if app_name:
            return run_applescript(f'tell application "{app_name}" to activate')

    return None