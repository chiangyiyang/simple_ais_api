import json
from datetime import datetime
import cloudscraper
from config import FAILED_LOG_FILE

# module-level scraper instance
SCRAPER = cloudscraper.create_scraper()

def safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default

def log_failed_record(record_data, error_message):
    try:
        with open(FAILED_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "timestamp": datetime.utcnow().isoformat(),
                "error": error_message,
                "data": record_data
            }, default=str, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"[ERROR] Failed to write to failed log: {e}")

def get_scraper():
    return SCRAPER