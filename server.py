import os
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
import cloudscraper
import json
from datetime import datetime
from flask_cors import CORS
from alarm import in_rectangle

# === Flask App & SQLite 設定 ===
# 初始化 Flask 應用程式
app = Flask(__name__)

# 對所有路由都開放所有來源
CORS(app)

# 設定 SQLite 資料庫路徑
os.makedirs('db', exist_ok=True)  # 確保 db 資料夾存在
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.abspath('db/ais_data.db')

# 禁用 SQLAlchemy 事件追蹤，避免佔用額外記憶體
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化 SQLAlchemy ORM
db = SQLAlchemy(app)

# === 失敗記錄檔案名稱 ===
# 用於儲存資料抓取過程中失敗的記錄
FAILED_LOG_FILE = "failed_records.json"

# === 工具：安全轉 float ===
# 將輸入值安全轉換為浮點數，若轉換失敗則返回預設值
def safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default

# === 工具：紀錄失敗資料 ===
# 將失敗的資料記錄寫入 JSON 檔案中，包含時間戳記、錯誤訊息和失敗的資料
def log_failed_record(record_data, error_message):
    try:
        with open(FAILED_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "timestamp": datetime.utcnow().isoformat(),
                "error": error_message,
                "data": record_data
            }) + "\n")
    except Exception as e:
        print(f"[ERROR] Failed to write to failed log: {e}")

# === SQLite 資料表定義 ===
# 定義船舶 AIS 資料表的結構
class ShipAIS(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    source = db.Column(db.String(200))
    ship_id = db.Column(db.String(50))
    shipname = db.Column(db.String(200))
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)
    speed = db.Column(db.Float)
    course = db.Column(db.Float)
    heading = db.Column(db.Float)
    rot = db.Column(db.Float)
    destination = db.Column(db.String(200))
    dwt = db.Column(db.String(50))
    flag = db.Column(db.String(50))
    shiptype = db.Column(db.String(50))
    gt_shiptype = db.Column(db.String(50))
    length = db.Column(db.String(50))
    width = db.Column(db.String(50))

    def to_dict(self):
        return {
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "ship_id": self.ship_id,
            "shipname": self.shipname,
            "lat": self.lat,
            "lon": self.lon,
            "speed": self.speed,
            "course": self.course,
            "heading": self.heading,
            "rot": self.rot,
            "destination": self.destination,
            "dwt": self.dwt,
            "flag": self.flag,
            "shiptype": self.shiptype,
            "gt_shiptype": self.gt_shiptype,
            "length": self.length,
            "width": self.width
        }

with app.app_context():
    db.create_all()

# === 抓取區塊 URL ===
urls = [
    "https://www.marinetraffic.com/getData/get_data_json_4/z:2/X:0/Y:0/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:2/X:0/Y:1/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:2/X:1/Y:0/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:2/X:1/Y:1/station:0",
]

# 監控矩形範圍（範例預設：台灣附近，請依需求修改）
RECT = {
    "min_lat": 21.5,
    "max_lat": 25.5,
    "min_lon": 119.5,
    "max_lon": 122.5
}

scraper = cloudscraper.create_scraper()

# === 抓資料並存入 DB ===
def fetch_data():
    with app.app_context():
        timestamp = datetime.utcnow()
        print(f"[{timestamp}] Fetching AIS data...")

        for url in urls:
            try:
                response = scraper.get(url)
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

                # 檢查剛存入的紀錄是否在 RECT 範圍內，若在則列印 SHIP_ID, SHIPNAME, LON, LAT
                try:
                    inserted = ShipAIS.query.filter_by(source=key, timestamp=timestamp).all()
                    for rec in inserted:
                        if in_rectangle(rec, RECT):
                            print(f"[ALARM] {rec.ship_id} | {rec.shipname} | {rec.lon} | {rec.lat}")
                except Exception as e_check:
                    print(f"[WARN] Alarm check failed for {key}: {e_check}")

            except Exception as e:
                print(f"Error fetching from {url}: {e}")

# === 啟動排程器：每 10 分鐘執行一次 ===
scheduler = BackgroundScheduler()
scheduler.add_job(func=fetch_data, trigger="interval", minutes=10)
scheduler.start()
fetch_data()  # 啟動時立即抓取一次

# === API: 最新每區塊船舶資料 ===
@app.route('/api/ais/latest', methods=['GET'])
def get_latest_data():
    results = {}
    for url in urls:
        key = url.replace('https://www.marinetraffic.com/getData/', '').replace('/', '_').replace(':', '_')
        latest = ShipAIS.query.filter_by(source=key).order_by(ShipAIS.timestamp.desc()).first()
        if latest:
            results[key] = latest.to_dict()
    return jsonify({
        "timestamp": datetime.utcnow().isoformat(),
        "results": results
    })

# === API: 查詢歷史資料 ===
@app.route('/api/ais/history', methods=['GET'])
def get_ship_history():
    try:
        query = ShipAIS.query

        if request.args.get("shipname"):
            query = query.filter(ShipAIS.shipname.ilike(f"%{request.args['shipname']}%"))
        if request.args.get("ship_id"):
            query = query.filter_by(ship_id=request.args["ship_id"])
        if request.args.get("start") and request.args.get("end"):
            start = datetime.fromisoformat(request.args.get("start"))
            end = datetime.fromisoformat(request.args.get("end"))
            query = query.filter(ShipAIS.timestamp.between(start, end))

        if (request.args.get("min_lat") and request.args.get("max_lat") and
            request.args.get("min_lon") and request.args.get("max_lon")):
            min_lat = safe_float(request.args.get("min_lat"))
            max_lat = safe_float(request.args.get("max_lat"))
            min_lon = safe_float(request.args.get("min_lon"))
            max_lon = safe_float(request.args.get("max_lon"))
            query = query.filter(
                ShipAIS.lat.between(min_lat, max_lat),
                ShipAIS.lon.between(min_lon, max_lon)
            )

        # results = [r.to_dict() for r in query.order_by(ShipAIS.timestamp.desc()).limit(500)]
        results = [r.to_dict() for r in query.order_by(ShipAIS.timestamp.desc())]
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# === 網頁：顯示船舶位置地圖 ===
@app.route('/')
def show_map():
    return app.send_static_file('ships_map.html')

# === 啟動 Flask 伺服器 ===
if __name__ == '__main__':
    app.run(port=5000)
