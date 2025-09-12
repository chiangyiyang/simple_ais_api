import os
import logging
from dotenv import load_dotenv
from linebot import LineBotApi
from linebot.exceptions import LineBotApiError
from linebot.models import TextSendMessage

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
if not CHANNEL_ACCESS_TOKEN:
    raise RuntimeError("LINE_CHANNEL_ACCESS_TOKEN not set in environment.")

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)

def send_msg(to: str, msg: str) -> bool:
    """Push a text message to the given recipient ID. Returns True on success."""
    if not to or not msg:
        raise ValueError("Both 'to' and 'msg' are required.")
    try:
        line_bot_api.push_message(to, TextSendMessage(text=msg))
    except LineBotApiError:
        logger.exception("Line API error while pushing message.")
        return False
    return True