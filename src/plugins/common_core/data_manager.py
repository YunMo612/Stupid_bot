import os
import json
from nonebot import logger

DATA_FILE = "bot_data.json"
BOT_DATA = {}

def load_data():
    global BOT_DATA
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            try:
                BOT_DATA = json.load(f)
            except Exception:
                pass
    
    # 初始化兜底数据
    for key in ["dev_users", "admin_users", "claimed_users"]:
        if key not in BOT_DATA: BOT_DATA[key] = []
    for key in ["bind_users", "checkin_records"]:
        if key not in BOT_DATA: BOT_DATA[key] = {}
        
    logger.success("📦 全局数据存储已挂载")

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(BOT_DATA, f, ensure_ascii=False, indent=4)

def get_data(key: str, default=None):
    return BOT_DATA.get(key, default)

def update_data(key: str, value):
    BOT_DATA[key] = value
    save_data()

# 启动时自动加载一次
load_data()
