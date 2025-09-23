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

# 失敗記錄檔
FAILED_LOG_FILE = os.getenv("FAILED_LOG_FILE", "failed_records.json")

# LINE 設定（可由環境變數提供）
LINE_USER_ID = os.getenv("LINE_USER_ID")
if not LINE_USER_ID:
    raise RuntimeError("LINE_USER_ID not set in environment.")

# 抓取間隔（分鐘）
FETCH_INTERVAL_MINUTES = int(os.getenv("FETCH_INTERVAL_MINUTES", "10"))