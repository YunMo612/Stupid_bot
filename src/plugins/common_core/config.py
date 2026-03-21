from nonebot import get_driver
from pydantic import BaseModel, Extra

class GlobalConfig(BaseModel, extra=Extra.ignore):
    # 自动从 .env 映射变量
    superusers: set = set()
    db_host: str = "127.0.0.1"
    db_port: int = 3306
    db_user: str = "root"
    db_pass: str = ""
    db_name: str = ""
    
    llama_server_url: str = "http://127.0.0.1:11434/v1/chat/completions"
    router_url: str = "http://127.0.0.1:11434/v1/chat/completions"

# 实例化全局配置对象
env_config = GlobalConfig(**get_driver().config.dict())
