import os
from dotenv import load_dotenv

load_dotenv()

# === 抓取區塊 URL ===
URLS = [
    "https://www.marinetraffic.com/getData/get_data_json_4/z:2/X:0/Y:0/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:2/X:0/Y:1/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:2/X:1/Y:0/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:2/X:1/Y:1/station:0",
]

# 監控矩形範圍（預設：台灣附近，必要時以環境變數或程式覆寫）
RECT = {
    "min_lat": float(os.getenv("RECT_MIN_LAT", 21.5)),
    "max_lat": float(os.getenv("RECT_MAX_LAT", 25.5)),
    "min_lon": float(os.getenv("RECT_MIN_LON", 119.5)),
    "max_lon": float(os.getenv("RECT_MAX_LON", 122.5)),
}

# 監控多邊形範圍（可選，預設 None，不啟用）
# 格式：[(lon1, lat1), (lon2, lat2), (lon3, lat3), ...]
POLYGON = None
# load from ./static/alarm_area.geojson if exists
import json
if os.path.exists("./static/alarm_area.geojson"):
    try:
        with open("./static/alarm_area.geojson", "r") as f:
            data = json.load(f)
            # load from GeoJSON format
            if data.get("type") == "FeatureCollection":
                features = data.get("features", [])
                if features:
                    geom = features[0].get("geometry", {})
                    if geom.get("type") == "Polygon":
                        POLYGON = geom.get("coordinates", [[]])[0]
    except Exception as e:
        print(f"[WARN] Failed to load alarm_polygon.json: {e}")

# 失敗記錄檔
FAILED_LOG_FILE = os.getenv("FAILED_LOG_FILE", "failed_records.json")

# LINE 設定（可由環境變數提供）
LINE_USER_ID = os.getenv("LINE_USER_ID")
if not LINE_USER_ID:
    raise RuntimeError("LINE_USER_ID not set in environment.")

# 抓取間隔（分鐘）
FETCH_INTERVAL_MINUTES = int(os.getenv("FETCH_INTERVAL_MINUTES", "10"))