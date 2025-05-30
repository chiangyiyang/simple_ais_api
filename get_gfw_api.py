
# 初始化客戶端
from datetime import datetime, timedelta
import gfwapiclient as gfw
import asyncio
from dotenv import load_dotenv
import os

load_dotenv()  # Load from .env automatically
access_token = os.getenv("GFW_ACCESS_TOKEN")


async def main():
    client = gfw.Client(access_token=access_token)
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=4)
    print(end_date, start_date)
    result = await client.events.get_all_events(
        datasets=["public-global-fishing-events:latest"],
        start_date=str(start_date),
        end_date=str(end_date),
        limit=2,  # 一天上限筆數（視需求調整）
        types=["FISHING"]
    )
    datas = result.data()
    for data in datas:
        print(type(data.model_dump_json()))
        print(data.model_dump_json())


asyncio.run(main())
