from app import create_app
from scheduler import start_scheduler
from fetcher import fetch_data
import os

app = create_app()

if __name__ == '__main__':
    # 啟動排程（以 app context 包裝 job）
    start_scheduler(app)
    # 啟動時立刻抓取一次（在 app context 中）
    fetch_data(app)
    app.run(port=int(os.getenv("PORT", "5000")))