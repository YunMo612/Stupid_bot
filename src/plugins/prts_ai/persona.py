# ==============================================================================
# 人设与配置热读取模块 (Persona & Config)
# ==============================================================================

import os
import json
from nonebot import logger

def load_ai_config() -> dict:
    """热读取运行参数 (温度、概率等)"""
    config_file = "ai_config.json"
    config = {
        "temperature": 0.6, 
        "top_p": 0.5, 
        "max_tokens": 8000, 
        "persona_settings": {"priestess_probability": 0.3, "chat_temp_threshold": 0.4}
    }
    
    if os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                config.update(loaded)
                if "persona_settings" in loaded: 
                    config["persona_settings"].update(loaded["persona_settings"])
        except Exception as e:
            logger.error(f"⚠️ ai_config.json 读取失败，使用默认参数: {e}")
    return config

def load_personas() -> dict:
    """热读取多重人格设定"""
    prompt_file = "ai_prompt.json"
    personas = {
        "base": {"chat": "你是随和的老玩家，不暴露是AI。", "tech": "你是技术群管，严谨高冷，不暴露是AI。"},
        "ghost": {},
        "win98": {}
    }

    if os.path.exists(prompt_file):
        try:
            with open(prompt_file, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
                def parse_p(data): return {k: ("\n".join(v) if isinstance(v, list) else str(v)) for k, v in data.items()}
                
                if "base" in raw_data: personas["base"].update(parse_p(raw_data["base"]))
                if "ghost" in raw_data: personas["ghost"].update(parse_p(raw_data["ghost"]))
                if "win98" in raw_data: personas["win98"].update(parse_p(raw_data["win98"]))
                elif "base" not in raw_data: personas["base"].update(parse_p(raw_data))
        except Exception as e:
            logger.error(f"⚠️ ai_prompt.json 读取失败: {e}")
    return personas