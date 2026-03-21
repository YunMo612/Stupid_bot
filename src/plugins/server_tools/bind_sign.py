# ==============================================================================
# 账号绑定与签到系统 (Bind & Sign)
# ==============================================================================

import random
import aiohttp
from datetime import datetime
from nonebot import on_command
from nonebot.rule import to_me
from nonebot.adapters.onebot.v11 import MessageEvent, GroupMessageEvent, Message
from nonebot.params import CommandArg, ArgPlainText
from nonebot.typing import T_State
from nonebot.exception import FinishedException

from ..common_core import get_data, update_data, get_db_connection

# --- 异步获取一言工具 ---
async def get_hitokoto() -> str:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://v1.hitokoto.cn/?c=c&c=a", timeout=5) as resp:
                data = await resp.json()
                return data.get("hitokoto", "新的一天也要充满活力哦！")
    except:
        return "新的一天也要充满活力哦！"

# ==================== A. 邮箱绑定 ====================
bind_matcher = on_command("绑定", rule=to_me())

@bind_matcher.handle()
async def handle_bind(event: MessageEvent, state: T_State, args: Message = CommandArg()):
    if isinstance(event, GroupMessageEvent):
        await bind_matcher.finish("⚠️ 为了保护账号安全，请在私信中使用绑定指令！")
        
    qq_id = str(event.get_user_id())
    bind_users = get_data("bind_users", {})
    
    if qq_id in bind_users:
        await bind_matcher.finish(f"⚠️ 你已经绑定过邮箱啦！\n当前绑定账号：{bind_users[qq_id]}\n如需换绑请联系腐竹。")
        
    email = args.extract_plain_text().strip()
    if not email:
        await bind_matcher.finish("⚠️ 请提供要绑定的皮肤站邮箱！\n👉 示例：/绑定 user@example.com")
        
    if email in bind_users.values():
        await bind_matcher.finish("❌ 该皮肤站邮箱已被其他 QQ 绑定！如果这不是你本人的操作，请联系腐竹。")
        
    try:
        async with get_db_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT uid FROM users WHERE email = %s", (email,))
                result = await cursor.fetchone()
                
        if not result:
            await bind_matcher.finish("❌ 未找到该邮箱对应的皮肤站账号！请确认你是否已在皮肤站注册。")
            
        state["target_email"] = email
    except FinishedException:
        raise
    except Exception as e:
        await bind_matcher.finish(f"🔴 数据库查询失败！\n原因：{e}")

# 多轮对话：等待用户二次确认
@bind_matcher.got("confirm_email", prompt="✅ 已在数据库中找到该账号！\n👉 请再次输入该邮箱以确认绑定：")
async def confirm_bind(event: MessageEvent, state: T_State, confirm_email: str = ArgPlainText("confirm_email")):
    if confirm_email.strip() != state["target_email"]:
        await bind_matcher.finish("❌ 两次输入的邮箱不一致，绑定已取消！请重新使用 /绑定 指令。")
        
    bind_users = get_data("bind_users", {})
    bind_users[str(event.get_user_id())] = state["target_email"]
    update_data("bind_users", bind_users)
    
    await bind_matcher.finish(f"🎉 绑定成功！\n当前绑定邮箱：{state['target_email']}\n你现在可以使用 /签到 每天获取积分了！")


# ==================== B. 每日签到 ====================
# 🌟 就是这一行刚才被不小心删掉了！现在补回来了！
sign_matcher = on_command("签到")

@sign_matcher.handle()
async def handle_sign(event: MessageEvent):
    qq_id = str(event.get_user_id())
    bind_users = get_data("bind_users", {})
    
    if qq_id not in bind_users:
        await sign_matcher.finish("⚠️ 你还没有绑定皮肤站账号！\n👉 请先【私聊我】发送：/绑定 你的注册邮箱")
        
    checkin_records = get_data("checkin_records", {})
    today = datetime.now().strftime("%Y-%m-%d")
    
    if checkin_records.get(qq_id) == today:
        await sign_matcher.finish("❌ 你今天已经签到过啦，明天再来吧！")
        
    email = bind_users[qq_id]
    add_score = random.randint(10, 50)
    current_score = "未知"
    
    try:
        async with get_db_connection() as conn:
            async with conn.cursor() as cursor:
                # 原子更新积分
                await cursor.execute("UPDATE users SET score = score + %s WHERE email = %s", (add_score, email))
                # 取出最新积分
                await cursor.execute("SELECT score FROM users WHERE email = %s", (email,))
                result = await cursor.fetchone()
                if result: current_score = result[0]
                
        # 更新 JSON 中的签到记录
        checkin_records[qq_id] = today
        update_data("checkin_records", checkin_records)
        
        hitokoto = await get_hitokoto()
        reply = f"[CQ:at,qq={qq_id}] ✅ 签到成功！\n🎲 本次获得积分：+{add_score}\n💰 当前总积分：{current_score}\n\n🌸 一言：{hitokoto}"
        
        # 发送成功消息
        await sign_matcher.finish(Message(reply))
        
    except FinishedException:
        # 拦截 finish 抛出的正常结束信号
        raise
    except Exception as e:
        await sign_matcher.finish(f"🔴 签到失败，数据库开小差了！\n原因：{e}")