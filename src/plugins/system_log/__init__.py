# ==============================================================================
# 系统日志持久化模块 (System Log)
# 负责：将控制台的实时日志按天分文件夹同步写入本地文件，生命周期 7 天
# ==============================================================================

import os
from nonebot import get_driver
from nonebot.log import logger
from nonebot.adapters import Event
from nonebot.message import run_preprocessor
from nonebot.matcher import Matcher
from nonebot.typing import T_State
from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="系统日志持久化 (System Log)",
    description="自动将 NoneBot 运行日志按天分文件夹写入，保留 7 天。",
    usage="后台自动运行，无需手动干预。",
    type="library",
)

# 基础日志目录
LOG_DIR = "logs"

# 🌟 核心魔法：向 NoneBot 底层的 loguru 添加文件输出管道
logger.add(
    os.path.join(LOG_DIR, "{time:YYYY-MM-DD}", "prts_run_{time:HH-mm-ss}.log"), 
    rotation="5 MB",
    retention="7 days",
    level="INFO",               
    encoding="utf-8",           
    enqueue=True,               
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{module}:{line} - {message}"
)

logger.success("📁 [基建] 实时日志持久化已挂载 (按天分拣 & 7天轮转模式)！")


# -------------------------------------------------------------------------
# API 调用拦截日志 — 记录关键 Bot API 调用
# -------------------------------------------------------------------------
_TRACKED_APIS = {
    "send_msg", "send_group_msg", "send_private_msg",
    "get_forward_msg", "send_group_forward_msg",
    "delete_msg", "set_group_kick", "set_group_ban",
}

driver = get_driver()

@driver.on_bot_connect
async def _register_api_hook(bot):
    @bot.on_calling_api
    async def _log_api_call(bot, api, data):
        if api in _TRACKED_APIS:
            target = data.get("group_id") or data.get("user_id") or ""
            logger.info(f"📡 [API 拦截] {api} → 目标: {target}")


# -------------------------------------------------------------------------
# 消息预处理日志 — 记录每条被匹配的事件
# -------------------------------------------------------------------------
@run_preprocessor
async def _log_preprocessor(matcher: Matcher, event: Event, state: T_State):
    plugin_name = matcher.plugin_name or "unknown"
    command = state.get("_prefix", {}).get("command", ())
    cmd_str = command[0] if command else ""
    user_id = getattr(event, "get_user_id", lambda: "?")()
    logger.debug(f"📋 [预处理] plugin={plugin_name} cmd={cmd_str} user={user_id}")