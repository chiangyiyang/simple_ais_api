from flask import Flask, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
import cloudscraper
import json
import time
from datetime import datetime

app = Flask(__name__)
scraper = cloudscraper.create_scraper()

# 記憶體中保存最新的資料
latest_data = {}

# 可自行調整的 URL 清單
urls = [
    "https://www.marinetraffic.com/getData/get_data_json_4/z:2/X:0/Y:0/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:2/X:0/Y:1/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:2/X:1/Y:0/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:2/X:1/Y:1/station:0",
]


def fetch_data():
    global latest_data
    timestamp = datetime.utcnow().isoformat()
    print(f"[{timestamp}] Fetching AIS data...")
    data_map = {}

    for url in urls:
        try:
            response = scraper.get(url)
            data = response.json()
            key = url.replace('https://www.marinetraffic.com/getData/', '').replace('/', '_').replace(':', '_')
            data_map[key] = data

            # 可選：將每筆儲存為 JSON 檔案
            with open(f"jsons/data_{key}_{int(time.time())}.json", 'w') as f:
                json.dump(data, f)

        except Exception as e:
            print(f"Error fetching from {url}: {e}")
            data_map[key] = {"error": str(e)}

    latest_data = {
        "timestamp": timestamp,
        "results": data_map
    }


# 初始化並設定定時任務
scheduler = BackgroundScheduler()
scheduler.add_job(func=fetch_data, trigger="interval", minutes=10)
scheduler.start()

# 啟動時先抓一次資料
fetch_data()

# REST API 路由
@app.route('/api/ais/latest', methods=['GET'])
def get_latest_data():
    return jsonify(latest_data)


if __name__ == "__main__":
    app.run(port=5000)
