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
    msg = message.lower()

    # Music
    if 'play' in msg and ('music' in msg or 'spotify' in msg or 'song' in msg):
        return run_applescript('tell application "Spotify" to play')
    if 'pause' in msg and ('music' in msg or 'spotify' in msg):
        return run_applescript('tell application "Spotify" to pause')
    if 'next' in msg and ('song' in msg or 'track' in msg):
        return run_applescript('tell application "Spotify" to next track')

    # Volume
    if 'volume up' in msg:
        return run_applescript('set volume output volume (output volume of (get volume settings) + 10)')
    if 'volume down' in msg:
        return run_applescript('set volume output volume (output volume of (get volume settings) - 10)')
    if 'mute' in msg:
        return run_applescript('set volume output muted true')
    if 'unmute' in msg:
        return run_applescript('set volume output muted false')

    # Calendar
    if 'calendar' in msg or 'next event' in msg or 'schedule' in msg:
        return run_applescript('''
            tell application "Calendar"
                set allEvents to every event of every calendar
                return "Calendar access granted"
            end tell''')

    # Screenshots
    if 'screenshot' in msg:
        path = os.path.expanduser('~/Desktop/jarvis_screenshot.png')
        subprocess.run(['screencapture', '-x', path])
        return f'Screenshot saved to Desktop as jarvis_screenshot.png'

    # Battery
    if 'battery' in msg:
        result = subprocess.run(['pmset', '-g', 'batt'], capture_output=True, text=True)
        return result.stdout.strip()

    # System stats
    if 'cpu' in msg or 'memory' in msg or 'ram' in msg:
        result = subprocess.run(['top', '-l', '1', '-n', '0'], capture_output=True, text=True)
        lines = result.stdout.split('\n')[:8]
        return '\n'.join(lines)

    # Notes
    if 'note' in msg or 'remind me' in msg:
        note_text = message.replace('note', '').replace('remind me', '').strip()
        script = f'tell application "Notes" to make new note with properties {{body:"{note_text}"}}'
        run_applescript(script)
        return f'Note saved: {note_text}'

    # Open apps
    if 'open' in msg:
        app_name = message.lower().replace('open', '').strip().title()
        return run_applescript(f'tell application "{app_name}" to activate')

    return None
