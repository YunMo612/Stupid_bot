# ==============================================================================
# 服务器状态查询 (Server Query)
# ==============================================================================

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Message
from nonebot.params import CommandArg

# 依赖第三方库 mcstatus
from mcstatus import JavaServer

status_matcher = on_command("服务器状态")

@status_matcher.handle()
async def handle_server_status(args: Message = CommandArg()):
    server_address = args.extract_plain_text().strip()
    
    if not server_address or "." not in server_address:
        await status_matcher.finish("⚠️ 格式不完整或未提供正确的服务器地址！\n👉 示例格式：/服务器状态 xxx.xxx.xxx")
    
    try:
        # 使用 mcstatus 进行异步 ping
        server = await JavaServer.async_lookup(server_address)
        status = await server.async_status()
        
        reply_msg = (
            f"🟢 服务器 [{server_address}] 当前运行中！\n"
            f"📶 延迟: {round(status.latency)}ms\n"
            f"👥 在线人数: {status.players.online}/{status.players.max}"
        )
        await status_matcher.finish(reply_msg)
        
    except Exception:
        await status_matcher.finish(f"🔴 哎呀，没联系上 [{server_address}] ...可能是地址拼写错误或离线啦！")