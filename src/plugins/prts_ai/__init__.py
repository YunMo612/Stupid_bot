# ==============================================================================
# PRTS AI 模块总控制台 (Controller)
# ==============================================================================

import re
# 🌟 关键修改：导入 on_message 和 to_me
from nonebot import on_message, logger, get_driver
from nonebot.rule import to_me
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, GroupMessageEvent, Message
from nonebot.exception import FinishedException

# 1. 导入公共工具箱
from ..common_core import env_config, get_data

# 2. 导入 AI 业务服务层与数据库层
from .llm_service import process_ai_request, clear_memory
from .database import init_db_pool, close_db_pool
from . import voice_handler

driver = get_driver()

# -------------------------------------------------------------------------
# 启动时初始化 AI 数据库连接池
# -------------------------------------------------------------------------
@driver.on_startup
async def _init_ai_db():
    await init_db_pool()

# -------------------------------------------------------------------------
# 启动时索引静态知识库
# -------------------------------------------------------------------------
@driver.on_startup
async def _index_knowledge():
    try:
        from .knowledge import ingest_docs
        import asyncio
        await asyncio.to_thread(ingest_docs)
    except Exception as e:
        logger.warning(f"⚠️ [知识库] 启动索引失败: {e}")

@driver.on_shutdown
async def shutdown():
    await close_db_pool()

# 🌟 关键修改：使用 on_message 和 rule=to_me()，必须被 @ 才会触发
# priority=99 确保所有 on_command 优先处理完毕后才轮到 AI
ai_matcher = on_message(rule=to_me(), priority=99, block=True)

@ai_matcher.handle()
async def handle_ai_entry(bot: Bot, event: MessageEvent):
    # 步骤 1：提取纯文本输入 (因为不用 on_command 了，所以不再使用 CommandArg)
    raw_prompt = event.get_plaintext().strip()

    # 🌟 关键修复：如果消息是指令格式（以 / 开头），跳过 AI 处理，避免与其他指令冲突
    if raw_prompt.startswith("/"):
        return
    
    # 兼容清理：如果用户 @bot 的同时还习惯性打字 "/ai 帮我查代码"，把前缀过滤掉
    for cmd in ["/ai", "ai", "问问", "大模型", "聊天", "看看"]:
        if raw_prompt.startswith(cmd):
            raw_prompt = raw_prompt[len(cmd):].strip()
            break
            
    is_group = isinstance(event, GroupMessageEvent)
    session_id = f"group_{event.group_id}" if is_group else f"private_{event.get_user_id()}"
    qq_id = str(event.get_user_id())

    # ==========================
    # 下面的代码（步骤 2 ~ 步骤 5）与你原来的一模一样，直接原样保留即可
    # ==========================
    
    # 步骤 2：指令解析器 (-h, -c, -t, -g, -win98)
    force_forward = False
    force_mode = None
    force_persona = None
    show_help = False

    while raw_prompt.startswith("-"):
        if raw_prompt.startswith("-win98"):
            force_persona = "win98"
            raw_prompt = re.sub(r'^-win98(?:\s+|$)', '', raw_prompt).strip()
            continue
            
        match = re.match(r'^-([cgth]+)(?:\s+|$)', raw_prompt)
        if match:
            flags = match.group(1)
            if 'h' in flags: show_help = True
            if 'g' in flags: force_forward = True
            if 'c' in flags: force_mode = "chat"
            if 't' in flags: force_mode = "tech"
            raw_prompt = raw_prompt[match.end():].strip()
        else:
            break 

    if show_help:
        help_msg = (
            "💡 【PRTS 终端指令使用指南】\n"
            "支持在提问前附加控制参数：\n"
            "-----------------------\n"
            "[-h] : 查看此说明书\n"
            "[-g] : 强制将回复折叠为[合并转发]\n"
            "[-c] : 强制锁定 [Chat 闲聊] 模式\n"
            "[-t] : 强制锁定 [Tech 技术] 模式\n"
            "[-win98] : 覆盖载入 [Windows 98] 人格\n"
            "-----------------------\n"
            "📝 示例：@Bot -win98 -tcg 帮我查代码"
        )
        await ai_matcher.finish(help_msg)

    # 步骤 3：拦截清空记忆指令
    if raw_prompt in ["清空上下文", "清除记忆", "重置对话", "重置"]:
        admins = set(get_data("admin_users", []))
        devs = set(get_data("dev_users", []))
        superusers = env_config.superusers
        if qq_id not in (admins | devs | superusers):
            await ai_matcher.finish("⛔ 权限不足！")
            
        await clear_memory(qq_id, session_id)
        await ai_matcher.finish("✨ 我的短期记忆已强制清空！")

    # 步骤 4：提取多模态附件 (图片, 文件, 转发)
    image_urls = []
    file_ids = []
    forward_ids = []
    
    for seg in event.message:
        if seg.type == "image":
            image_urls.append(seg.data.get("url"))
        elif seg.type in ["file", "offline_file"]:
            file_ids.append(seg.data.get("file_id") or seg.data.get("file"))
        elif seg.type == "forward":
            forward_ids.append(seg.data.get("id"))

    reply_text = ""
    if event.reply:
        reply_msg = event.reply.message
        reply_text = reply_msg.extract_plain_text().strip()
        for seg in reply_msg:
            if seg.type == "image":
                image_urls.append(seg.data.get("url"))
            elif seg.type in ["file", "offline_file"]:
                file_ids.append(seg.data.get("file_id") or seg.data.get("file"))
            elif seg.type == "forward":
                forward_ids.append(seg.data.get("id"))

    if not raw_prompt and not image_urls and not file_ids and not forward_ids:
        await ai_matcher.finish("⚠️ 请输入你要问的问题，或附带图片/文件！")

    # 步骤 5：移交大模型核心
    try:
        await process_ai_request(
            bot=bot,
            event=event,
            matcher=ai_matcher,
            raw_prompt=raw_prompt,
            reply_text=reply_text,
            force_forward=force_forward,
            force_mode=force_mode,
            force_persona=force_persona,
            image_urls=image_urls,
            file_ids=file_ids,
            forward_ids=forward_ids,
            session_id=session_id,
            qq_id=qq_id,
            is_group=is_group
        )
    except FinishedException:
        raise 
    except Exception as e:
        logger.error(f"AI 调度服务异常: {e}")
        await ai_matcher.finish(f"🔴 AI 核心异常：{str(e)}")