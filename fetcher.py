from datetime import datetime
from app import db, create_app
from models import ShipAIS
from config import URLS, RECT, LINE_USER_ID
from utils import safe_float, log_failed_record, get_scraper
from alarm import in_rectangle
from line_msg import send_msg
import os

SCRAPER = get_scraper()

def fetch_data(app=None):
    # Optional app context caller: if app provided, use it; otherwise assume caller provides context.
    if app:
        ctx = app.app_context()
        ctx.__enter__()

    try:
        timestamp = datetime.utcnow()
        print(f"[{timestamp}] Fetching AIS data...")

        for url in URLS:
            try:
                response = SCRAPER.get(url)
                data = response.json()
                key = url.replace('https://www.marinetraffic.com/getData/', '').replace('/', '_').replace(':', '_')

                for row in data["data"].get("rows", []):
                    try:
                        record = ShipAIS(
                            timestamp=timestamp,
                            source=key,
                            ship_id=row.get("SHIP_ID"),
                            shipname=row.get("SHIPNAME"),
                            lat=safe_float(row.get("LAT")),
                            lon=safe_float(row.get("LON")),
                            speed=safe_float(row.get("SPEED")) / 10,
                            course=safe_float(row.get("COURSE")),
                            heading=safe_float(row.get("HEADING")),
                            rot=safe_float(row.get("ROT")),
                            destination=row.get("DESTINATION"),
                            dwt=row.get("DWT"),
                            flag=row.get("FLAG"),
                            shiptype=row.get("SHIPTYPE"),
                            gt_shiptype=row.get("GT_SHIPTYPE"),
                            length=row.get("LENGTH"),
                            width=row.get("WIDTH")
                        )
                        db.session.add(record)
                    except Exception as row_error:
                        log_failed_record(row, str(row_error))
                        print(f"[WARN] Failed to parse ship row: {row.get('SHIPNAME')} - {row_error}")

                db.session.commit()

                # Alarm check
                try:
                    msg = ''
                    inserted = ShipAIS.query.filter_by(source=key, timestamp=timestamp).all()
                    for rec in inserted:
                        if in_rectangle(rec, RECT):
                            print(f"[ALARM] {rec.ship_id} | {rec.shipname} | {rec.lon} | {rec.lat}")
                            msg += f"[ALARM] {rec.ship_id} | {rec.shipname} | {rec.lon} | {rec.lat}\n"
                    if msg and LINE_USER_ID:
                        send_msg(LINE_USER_ID, msg)
                except Exception as e_check:
                    print(f"[WARN] Alarm check failed for {key}: {e_check}")

            except Exception as e:
                print(f"Error fetching from {url}: {e}")
    finally:
        if app:
            ctx.__exit__(None, None, None)