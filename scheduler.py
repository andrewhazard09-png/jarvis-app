import schedule
import time
import subprocess
import os

def run_improver():
    print('◈ RUNNING NIGHTLY IMPROVEMENT...')
    subprocess.run(['python3', 'improver.py'], cwd=os.path.expanduser('~/jarvis-app'))

# Run every night at 2am
schedule.every().day.at("02:00").do(run_improver)

# Also run once on startup to test
print('◈ SCHEDULER ONLINE — IMPROVEMENT RUNS AT 2AM NIGHTLY')
print('◈ Running test cycle now...')
run_improver()

while True:
    schedule.run_pending()
    time.sleep(60)
