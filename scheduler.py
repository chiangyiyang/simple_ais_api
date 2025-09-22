from apscheduler.schedulers.background import BackgroundScheduler
from config import FETCH_INTERVAL_MINUTES
from fetcher import fetch_data

scheduler = BackgroundScheduler()

def start_scheduler(app=None):
    # schedule fetch_data with optional app context wrapper
    if app:
        scheduler.add_job(func=lambda: fetch_data(app), trigger="interval", minutes=FETCH_INTERVAL_MINUTES, id="fetch_job", replace_existing=True)
    else:
        scheduler.add_job(func=fetch_data, trigger="interval", minutes=FETCH_INTERVAL_MINUTES, id="fetch_job", replace_existing=True)
    scheduler.start()

def stop_scheduler():
    scheduler.shutdown(wait=False)