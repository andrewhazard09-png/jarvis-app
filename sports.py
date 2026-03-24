import requests

SPORTS = {
    'nba': 'basketball/nba',
    'nfl': 'football/nfl',
    'mlb': 'baseball/mlb',
    'nhl': 'hockey/nhl',
    'ncaa': 'basketball/mens-college-basketball',
    'soccer': 'soccer/usa.1',
    'mls': 'soccer/usa.1',
}

def get_scores(sport='nba'):
    try:
        league = SPORTS.get(sport.lower(), 'basketball/nba')
        url = f'https://site.api.espn.com/apis/site/v2/sports/{league}/scoreboard'
        res = requests.get(url, timeout=10)
        events = res.json().get('events', [])
        if not events:
            return f'No {sport.upper()} games found today.'
        lines = [f'{sport.upper()} scores:']
        for e in events:
            comp = e['competitions'][0]
            status = comp['status']['type']['shortDetail']
            teams = comp['competitors']
            home = next(t for t in teams if t['homeAway'] == 'home')
            away = next(t for t in teams if t['homeAway'] == 'away')
            home_name = home['team']['abbreviation']
            away_name = away['team']['abbreviation']
            home_score = home.get('score', '')
            away_score = away.get('score', '')
            if home_score and away_score:
                lines.append(f'  {away_name} {away_score} @ {home_name} {home_score} — {status}')
            else:
                lines.append(f'  {away_name} @ {home_name} — {status}')
        return '\n'.join(lines)
    except Exception as e:
        return f'Sports data unavailable: {str(e)}'

def detect_sport(message):
    msg = message.lower()
    if 'wbc' in msg or 'world baseball classic' in msg: return 'mlb'
    if 'nfl' in msg or 'football' in msg: return 'nfl'
    if 'mlb' in msg or 'baseball' in msg: return 'mlb'
    if 'nhl' in msg or 'hockey' in msg: return 'nhl'
    if 'mls' in msg or 'soccer' in msg: return 'mls'
    if 'college' in msg or 'ncaa' in msg: return 'ncaa'
    return 'nba'
