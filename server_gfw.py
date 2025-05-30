import os
import json
from datetime import datetime
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
from apscheduler.schedulers.background import BackgroundScheduler
import asyncio
import gfwapiclient as gfw
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

load_dotenv()  # Load from .env automatically
access_token = os.getenv("GFW_ACCESS_TOKEN")


# 初始化 Flask 與 DB 設定
app = Flask(__name__)
CORS(app)
os.makedirs('db', exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + \
    os.path.abspath('db/gfw_data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# GFW 事件資料表


class GFWEvent(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    type = db.Column(db.String(50))
    start = db.Column(db.DateTime)
    end = db.Column(db.DateTime)
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)
    vessel_id = db.Column(db.String(50))
    vessel_name = db.Column(db.String(200))
    vessel_ssvid = db.Column(db.String(50))
    vessel_flag = db.Column(db.String(50))
    vessel_type = db.Column(db.String(50))
    bounding_box = db.Column(SQLITE_JSON)
    regions = db.Column(SQLITE_JSON)
    distances = db.Column(SQLITE_JSON)
    public_authorizations = db.Column(SQLITE_JSON)
    fishing_info = db.Column(SQLITE_JSON)
    raw_json = db.Column(db.Text)

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "start": self.start.isoformat() if self.start else None,
            "end": self.end.isoformat() if self.end else None,
            "lat": self.lat,
            "lon": self.lon,
            "vessel_id": self.vessel_id,
            "vessel_name": self.vessel_name,
            "vessel_ssvid": self.vessel_ssvid,
            "vessel_flag": self.vessel_flag,
            "vessel_type": self.vessel_type,
            "bounding_box": self.bounding_box,
            "regions": self.regions,
            "distances": self.distances,
            "public_authorizations": self.public_authorizations,
            "fishing_info": self.fishing_info,
            "raw_json": self.raw_json
        }


# 初始化 DB
with app.app_context():
    db.create_all()

# 存一筆 GFW event


def save_gfw_event(event_json):
    # 判斷有沒有已存過
    if db.session.get(GFWEvent, event_json.get("id")):
        return
    event = GFWEvent(
        id=event_json.get("id"),
        type=event_json.get("type"),
        start=datetime.fromisoformat(event_json.get("start").replace(
            "Z", "+00:00")) if event_json.get("start") else None,
        end=datetime.fromisoformat(event_json.get("end").replace(
            "Z", "+00:00")) if event_json.get("end") else None,
        lat=event_json.get("position", {}).get("lat"),
        lon=event_json.get("position", {}).get("lon"),
        vessel_id=event_json.get("vessel", {}).get("id"),
        vessel_name=event_json.get("vessel", {}).get("name"),
        vessel_ssvid=event_json.get("vessel", {}).get("ssvid"),
        vessel_flag=event_json.get("vessel", {}).get("flag"),
        vessel_type=event_json.get("vessel", {}).get("type"),
        bounding_box=event_json.get("bounding_box"),
        regions=event_json.get("regions"),
        distances=event_json.get("distances"),
        public_authorizations=event_json.get(
            "vessel", {}).get("public_authorizations"),
        fishing_info=event_json.get("fishing"),
        raw_json=json.dumps(event_json, ensure_ascii=False)
    )
    db.session.add(event)
    db.session.commit()

# 定時自動下載 GFW 資料


def fetch_gfw_events():
    print(f"[{datetime.utcnow().isoformat()}] Fetching GFW events for last 4 days ...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(fetch_and_store_gfw_events())
    loop.close()


async def fetch_and_store_gfw_events():
    try:
        client = gfw.Client(access_token=access_token)
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=4)
        result = await client.events.get_all_events(
            datasets=["public-global-fishing-events:latest"],
            start_date=str(start_date),
            end_date=str(end_date),
            limit=20,  # 一天上限筆數（視需求調整）
            types=["FISHING"]
        )
        with app.app_context():
            for event in result.data():
                event_dict = json.loads(event.model_dump_json())
                save_gfw_event(event_dict)
        print(
            f"[GFW] Downloaded and saved {len(result.data())} events from {start_date} to {end_date}.")
    except Exception as e:
        print(f"[GFW] Error: {e}")

# 啟動排程器：每 24 小時執行一次
scheduler = BackgroundScheduler()
scheduler.add_job(func=fetch_gfw_events, trigger="interval", days=1)
scheduler.start()
fetch_gfw_events()  # 啟動時自動抓一次

# API: 查詢 GFW 事件


@app.route('/api/gfw/events', methods=['GET'])
def get_gfw_events():
    query = GFWEvent.query
    if request.args.get("vessel_name"):
        query = query.filter(GFWEvent.vessel_name.ilike(
            f"%{request.args['vessel_name']}%"))
    if request.args.get("flag"):
        query = query.filter_by(vessel_flag=request.args["flag"])
    if request.args.get("type"):
        query = query.filter_by(type=request.args["type"])
    if request.args.get("start") and request.args.get("end"):
        try:
            start = datetime.fromisoformat(request.args.get("start"))
            end = datetime.fromisoformat(request.args.get("end"))
            query = query.filter(GFWEvent.start.between(start, end))
        except Exception as e:
            return jsonify({"error": "Invalid date format"}), 400
    results = [r.to_dict()
               for r in query.order_by(GFWEvent.start.desc()).limit(100)]
    return jsonify(results)


@app.route('/')
def home():
    return 'GFW Fishing Event API Server'


if __name__ == '__main__':
    app.run(port=5000)
