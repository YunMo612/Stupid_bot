from nonebot import get_app
from fastapi import Request, HTTPException
import json

# 获取 NoneBot 底层的 FastAPI 实例
app = get_app()

# 我们将在 llm_service 里实现这个核心逻辑
# from .llm_service import generate_ai_reply 

@app.post("/api/ai/chat")
async def external_ai_chat(request: Request):
    """
    提供给外部服务 (如网站、MC服务器) 的 RESTful API 接口
    格式: {"prompt": "你好", "mode": "chat", "user_id": "api_user_1"}
    """
    try:
        data = await request.json()
        prompt = data.get("prompt")
        user_id = data.get("user_id", "external_api")
        
        if not prompt:
            raise HTTPException(status_code=400, detail="Missing 'prompt' in body")
            
        # 这里直接调用我们将要重构的服务层函数 (解耦了 QQ 相关的逻辑)
        # reply = await generate_ai_reply(prompt=prompt, session_id=user_id)
        
        # 预留占位返回
        reply = "这是来自 PRTS AI 模块的 API 响应。大模型服务正在接入中..."
        
        return {
            "status": "success",
            "reply": reply
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
# 唤醒暴露给外部的 FastAPI 接口
from . import web_api