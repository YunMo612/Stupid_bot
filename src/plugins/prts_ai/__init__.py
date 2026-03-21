# ==============================================================================
# PRTS AI 模块总控制台 (Controller)
# ==============================================================================

import re
from nonebot import on_command, logger
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, GroupMessageEvent, Message
from nonebot.params import CommandArg
from nonebot.exception import FinishedException

# 1. 导入公共工具箱
from ..common_core import env_config, get_data

# 2. 导入 AI 业务服务层
from .llm_service import process_ai_request, clear_memory

# 🌟 修复区：彻底移除了 to_me，设置了优先级，确保只要开头是 /ai 绝对拦截
ai_matcher = on_command("ai", aliases={"问问", "大模型", "聊天", "看看"}, priority=2, block=True)

@ai_matcher.handle()
async def handle_ai_entry(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
    # 步骤 1：提取纯文本输入
    raw_prompt = args.extract_plain_text().strip()
    if not raw_prompt:
        full_text = event.get_plaintext()
        for cmd in ["ai", "问问", "大模型", "聊天", "看看"]:
            if cmd in full_text:
                full_text = full_text.replace(cmd, "", 1)
        raw_prompt = full_text.strip()
        
    is_group = isinstance(event, GroupMessageEvent)
    session_id = f"group_{event.group_id}" if is_group else f"private_{event.get_user_id()}"
    qq_id = str(event.get_user_id())

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
            "📝 示例：/ai -win98 -tcg 帮我查代码"
        )
        await ai_matcher.finish(help_msg)

    # 步骤 3：拦截清空记忆指令
    if raw_prompt in ["清空上下文", "清除记忆", "重置对话", "重置"]:
        admins = set(get_data("admin_users", []))
        devs = set(get_data("dev_users", []))
        superusers = env_config.superusers
        if qq_id not in (admins | devs | superusers):
            await ai_matcher.finish("⛔ 权限不足！")
            
        clear_memory(session_id)
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

# 🌟 修复区：暂时注释掉 web_api 的加载，防止它缺少环境导致连环崩溃
# from . import web_api