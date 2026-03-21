# ==============================================================================
# 邀请码分发系统 (Invite System)
# ==============================================================================

import uuid
from datetime import datetime
from nonebot import on_command
from nonebot.rule import to_me
from nonebot.adapters.onebot.v11 import MessageEvent, GroupMessageEvent

# 💡 极其优雅的基建调用，只需一句导入
from ..common_core import get_data, update_data, get_db_connection

invite_matcher = on_command("获取邀请码", rule=to_me(), aliases={"获取验证码", "邀请码"})

@invite_matcher.handle()
async def handle_invite_code(event: MessageEvent):
    if isinstance(event, GroupMessageEvent):
        await invite_matcher.finish("⚠️ 为了保护你的邀请码安全，请在私信（或群临时会话）中向我发送暗号获取！")
        
    user_id = str(event.get_user_id()) 
    claimed_users = get_data("claimed_users", [])
    
    if user_id in claimed_users:
        await invite_matcher.finish("❌ 你已经领取过邀请码啦！如果忘记了请联系腐竹。")
    
    new_code = uuid.uuid4().hex
    now_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        # 🌟 基建魔法：异步数据库直连
        async with get_db_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("INSERT INTO invitation_codes (code, generated_at) VALUES (%s, %s)", (new_code, now_time))
                
        # 🌟 基建魔法：安全地更新本地 JSON
        claimed_users.append(user_id)
        update_data("claimed_users", claimed_users)
        
        await invite_matcher.finish(f"🎉 欢迎来到新世界！\n你的专属皮肤站注册邀请码是：\n{new_code}\n👉 请尽快在皮肤站注册使用哦！")
        
    except Exception as e:
        await invite_matcher.finish(f"🔴 数据库写入失败！\n原因：{e}")