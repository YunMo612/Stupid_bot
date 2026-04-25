from nonebot import get_driver
from pydantic import BaseModel, ConfigDict

class GlobalConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    # 自动从 .env 映射变量
    superusers: set = set()
    db_host: str = "127.0.0.1"
    db_port: int = 3306
    db_user: str = "root"
    db_pass: str = ""
    db_name: str = ""
    
    llama_server_url: str = "http://127.0.0.1:11434/v1/chat/completions"
    router_url: str = "http://127.0.0.1:11434/v1/chat/completions"

    # AI 模块专属配置
    ai_db_name: str = "stupid_db"
    uid_salt: str = "PRTS_SECRET_!@#"
    mempalace_path: str = ""
    melotts_api_url: str = "http://127.0.0.1:8082"

# 实例化全局配置对象
env_config = GlobalConfig(**get_driver().config.model_dump())
