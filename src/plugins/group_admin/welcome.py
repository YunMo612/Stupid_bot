# ==============================================================================
# 智能群聊迎新 (Welcome)
# ==============================================================================

import os
import json
import aiohttp
from nonebot import on_notice, logger
from nonebot.adapters.onebot.v11 import Bot, GroupIncreaseNoticeEvent, Message

# 💡 借用核心基建里的 API 路由地址
from ..common_core import env_config

welcome_matcher = on_notice()

@welcome_matcher.handle()
async def handle_group_increase(bot: Bot, event: GroupIncreaseNoticeEvent):
    user_id = str(event.get_user_id())
    group_id = event.group_id
    
    # 防止机器人自己进群时触发欢迎
    if user_id == str(event.self_id):
        return

    # 尝试从本地 JSON 提取 chat 人设 (兜底为普通老玩家)
    prompt_file = "ai_prompt.json" 
    custom_persona = "你是 Minecraft 玩家交流群里一位随和、靠谱的老玩家。"
    
    if os.path.exists(prompt_file):
        try:
            with open(prompt_file, "r", encoding="utf-8") as f:
                p = json.load(f)
                custom_persona = p.get("base", {}).get("chat", custom_persona) if "base" in p else p.get("chat", custom_persona)
        except Exception:
            pass
            
    # 针对小模型优化的极致短指令
    sys_prompt = (
        f"{custom_persona}\n\n"
        f"[指令：群里刚来了一位新玩家。请用符合你人设的语气说一句欢迎的话。"
        f"要求：必须在15个字以内！绝对不要带引号！不要说多余的废话！直接输出这句欢迎语！]"
    )
    
    payload = {
        "model": "qwen2.5-0.5b",  
        "messages": [
            {"role": "system", "content": sys_prompt}, 
            {"role": "user", "content": "来新人了，快说一句欢迎语！"}
        ], 
        "temperature": 0.8, 
        "max_tokens": 30          
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            # 动态使用环境变量里的 ROUTER_URL
            async with session.post(env_config.router_url, json=payload, timeout=5) as response:
                if response.status == 200:
                    ai_reply = (await response.json())["choices"][0]["message"]["content"].strip()
                    if ai_reply.startswith(('"', '“')) and ai_reply.endswith(('"', '”')):
                        ai_reply = ai_reply[1:-1]
                    await bot.send_group_msg(group_id=group_id, message=Message(f"[CQ:at,qq={user_id}] {ai_reply}"))
                else:
                    raise Exception(f"模型节点异常，状态码: {response.status}")
    except Exception as e:
        logger.warning(f"智能迎新请求失败，使用兜底文本。原因: {e}")
        fallback_msg = f"[CQ:at,qq={user_id}] 欢迎加入服务器群聊！"
        await bot.send_group_msg(group_id=group_id, message=Message(fallback_msg))