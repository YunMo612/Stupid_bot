import os
import httpx
import tempfile
from nonebot import on_notice, on_message, get_driver
from nonebot.log import logger
from nonebot.rule import to_me
from nonebot.adapters.onebot.v11 import Bot, NoticeEvent, GroupMessageEvent, MessageSegment

# ==========================================
# ⚙️ 核心配置：连接物理机的 FastAPI
# ==========================================
# 默认指向物理机的 8082 端口 (基于你提供的 main.py)
MELOTTS_API_URL = get_driver().config.dict().get("melotts_api_url", "http://10.0.2.2:8082")

async def request_melotts(text: str) -> str:
    """向物理机的 FastAPI 请求语音合成，返回虚拟机的本地音频路径"""
    logger.info(f"正在向物理机请求 TTS 合成: {text}")
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            payload = {"text": text, "speed": 1.0}
            response = await client.post(MELOTTS_API_URL, json=payload)
            
            if response.status_code == 200:
                fd, temp_path = tempfile.mkstemp(suffix=".wav")
                with os.fdopen(fd, 'wb') as f:
                    f.write(response.content)
                logger.success(f"TTS 音频已成功接收并保存至: {temp_path}")
                return temp_path
            else:
                logger.error(f"物理机 TTS 服务返回错误: {response.text}")
                return None
    except Exception as e:
        logger.error(f"无法连接到物理机 TTS 服务，请检查网络或端口 8082: {e}")
        return None

# ==========================================
# 🛡️ 方案 A：100% 稳定的语音条 (PTT) 回复方案
# 触发方式：在群里 @机器人 说一段话
# ==========================================
ai_voice_chat = on_message(rule=to_me(), priority=98, block=False)

@ai_voice_chat.handle()
async def handle_ai_voice_message(bot: Bot, event: GroupMessageEvent):
    user_text = event.get_plaintext().strip()
    if not user_text:
        return

    # 跳过指令消息，避免与其他指令冲突
    if user_text.startswith("/"):
        return

    # 这里可以接入你的 LLM 逻辑
    # ai_text = await get_llm_response(user_text)
    ai_text = f"你刚才说了：{user_text}。物理机语音合成模块运转正常！"
    
    audio_path = await request_melotts(ai_text)
    
    if audio_path:
        try:
            logger.info("正在将生成的音频作为语音条(PTT)发送到群聊...")
            await bot.send(event, MessageSegment.record(f"file://{audio_path}"))
            os.remove(audio_path) # 发送完毕清理垃圾
        except Exception as e:
            logger.error(f"发送语音条失败: {e}")

# ==========================================
# 🕵️ 间谍探针：抓取真实的底层事件名
# ==========================================
debug_notice = on_notice(priority=1, block=False)

@debug_notice.handle()
async def spy_all_notice(event: NoticeEvent):
    """
    无差别打印所有的 Notice 事件。
    当你在手机上发起群语音时，盯着控制台看这行日志打印了什么 notice_type！
    """
    logger.debug(f"【间谍探针】捕获到通知事件: {event.json()}")

# ==========================================
# 📞 方案 B：实时语音接听与推流 (依赖框架兼容性)
# ==========================================
voice_call_handler = on_notice(priority=5, block=False)

@voice_call_handler.handle()
async def handle_qq_voice_call(bot: Bot, event: NoticeEvent):
    notice_type = event.notice_type
    
    # 1. 拦截私聊语音
    if notice_type in ["friend_call", "private_call"]: 
        logger.info(f"检测到私聊语音邀请，尝试自动挂断。发起人: {event.user_id}")
        try:
            await bot.call_api("reject_call", call_id=getattr(event, "call_id", ""))
        except Exception as e:
            logger.error(f"自动挂断私聊失败: {e}")
        return

    # 2. 尝试接听群聊语音 (注意：这里的 group_call 可能需要换成你抓包到的真实事件名)
    if notice_type == "group_call":
        group_id = getattr(event, "group_id", 0)
        logger.info(f"检测到群 {group_id} 语音邀请，准备接通！")
        
        try:
            await bot.call_api("join_group_call", group_id=group_id)
            logger.info("✅ 已发出接通群语音指令。")
            
            ai_text = "大家好，我是 PRTS。我已经接入本群语音频道。"
            audio_path = await request_melotts(ai_text)
            
            if audio_path:
                logger.info("准备推流音频到语音频道...")
                await bot.call_api("send_group_call_audio", group_id=group_id, file=f"file://{audio_path}")
                try:
                    os.remove(audio_path)
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"❌ 群语音处理链路崩溃 (底层框架可能不支持该 API): {e}")