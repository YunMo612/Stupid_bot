import urllib.parse
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import nonebot
from nonebot import get_driver

# 拿到 NoneBot 底层的 FastAPI 实例
app: FastAPI = nonebot.get_app()

# 从环境变量读取 TTS 地址
MELOTTS_API_URL = getattr(get_driver().config, "melotts_api_url", "http://127.0.0.1:8082")

# 定义外部设备传过来的数据格式
class DeviceRequest(BaseModel):
    text: str
    device_id: str = "default_device"

# 假设你在 llm_service.py 已经写好了大模型调用的函数
# from .llm_service import get_llm_reply

@app.post("/api/device/chat")
async def device_chat_endpoint(req: DeviceRequest):
    # 1. 将外部设备的文本交给大模型处理
    # llm_text = await get_llm_reply(req.text) 
    llm_text = f"收到设备 {req.device_id} 的指令，这是测试回复。" # 替换为你真实的大模型调用
    
    # 2. 准备物理机 MeloTTS 的接口地址
    tts_api_url = MELOTTS_API_URL
    tts_payload = {"text": llm_text, "language": "ZH"} # 根据你的 MeloTTS 接口文档调整
    
    # 3. 创建异步音频流生成器 (透传魔法)
    async def audio_stream_generator():
        async with httpx.AsyncClient(timeout=60.0) as client:
            # 使用 .stream() 建立流式连接，不一次性吃掉所有内存
            async with client.stream("POST", tts_api_url, json=tts_payload) as response:
                if response.status_code != 200:
                    yield b"TTS Engine Error"
                    return
                
                # 物理机吐出多少字节，我们就给外部设备转发多少字节
                async for chunk in response.aiter_bytes(chunk_size=4096):
                    yield chunk

    # 4. 把中文文本进行 URL 编码，塞进 Header
    # 注意：HTTP Header 默认不支持中文，必须 quote 编码
    encoded_text = urllib.parse.quote(llm_text)

    # 5. 组合并返回流式响应
    return StreamingResponse(
        audio_stream_generator(),
        media_type="audio/wav", # 如果你返回的是 mp3，请改为 audio/mpeg
        headers={
            "X-LLM-Reply": encoded_text,  # 外部设备从这里读取文本
            "Access-Control-Expose-Headers": "X-LLM-Reply" # 允许前端或设备跨域读取该 Header
        }
    )