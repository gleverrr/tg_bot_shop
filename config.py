import os
from dotenv import load_dotenv

load_dotenv()

class Config:

    BOT_TOKEN = os.getenv('BOT_TOKEN')
    DATABASE_URL = os.getenv('DATABASE_URL')
    CHANNEL_LINK = os.getenv('CHANNEL_LINK')
    CHAT_LINK = os.getenv('CHAT_LINK')
    CHANNEL_ID=os.getenv('CHANNEL_ID')
    ADMIN_IDS = list(map(int, os.getenv('ADMIN_IDS', '').split(','))) if os.getenv('ADMIN_IDS') else []