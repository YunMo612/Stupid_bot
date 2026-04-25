# ==============================================================================
# 广播指令 (Broadcast)
# 负责：管理员向群聊广播消息
# ==============================================================================

import re
from nonebot import on_command, logger
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, GroupMessageEvent, Message
from nonebot.params import CommandArg

from ..common_core import get_data, env_config


# --- 权限校验（复用 admin_cmd 同级逻辑） ---
def _check_admin(qq_id: str) -> bool:
    devs = set(get_data("dev_users", [])) | env_config.superusers
    admins = set(get_data("admin_users", []))
    return qq_id in (admins | devs)


broadcast_cmd = on_command("广播", priority=1, block=True)


@broadcast_cmd.handle()
async def handle_broadcast(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
    # 仅私聊
    if isinstance(event, GroupMessageEvent):
        await broadcast_cmd.finish("⚠️ 请在私聊中使用！")
    # 权限校验
    if not _check_admin(str(event.get_user_id())):
        await broadcast_cmd.finish("⛔ 权限不足！")

    raw = args.extract_plain_text().strip()
    if not raw:
        await broadcast_cmd.finish(
            "⚠️ 用法：/广播 {消息} [-群号] [-不匿名]\n"
            "示例：/广播 服务器今晚维护 -123456789\n"
            "示例：/广播 新版本上线啦 -不匿名"
        )

    # ---- 解析参数 ----
    target_group: int | None = None
    anonymous: bool = True

    # 匹配 -数字 (群号)
    group_match = re.search(r"-(\d{5,})", raw)
    if group_match:
        target_group = int(group_match.group(1))
        raw = raw[:group_match.start()] + raw[group_match.end():]

    # 匹配 -不匿名 / -非匿名 / -署名
    if re.search(r"-(不匿名|非匿名|署名)", raw):
        anonymous = False
        raw = re.sub(r"-(不匿名|非匿名|署名)", "", raw)

    content = raw.strip()
    if not content:
        await broadcast_cmd.finish("⚠️ 广播内容不能为空！")

    # ---- 构建广播消息 ----
    msg = f"📢 【广播通知】\n{content}"

    if not anonymous:
        try:
            info = await bot.get_stranger_info(user_id=event.get_user_id())
            nickname = info.get("nickname", "未知")
        except Exception:
            nickname = "未知"
        msg += f"\n\n—— {nickname}({event.get_user_id()})"

    # ---- 发送 ----
    if target_group:
        # 指定群
        try:
            await bot.send_group_msg(group_id=target_group, message=msg)
            await broadcast_cmd.finish(f"✅ 广播已发送至群 [{target_group}]。")
        except Exception as e:
            await broadcast_cmd.finish(f"🔴 发送失败：{e}")
    else:
        # 全部群
        try:
            group_list = await bot.get_group_list()
        except Exception as e:
            await broadcast_cmd.finish(f"🔴 获取群列表失败：{e}")

        success, fail = 0, 0
        for g in group_list:
            gid = g.get("group_id")
            try:
                await bot.send_group_msg(group_id=gid, message=msg)
                success += 1
            except Exception as e:
                fail += 1
                logger.warning(f"广播发送至群 {gid} 失败: {e}")

        await broadcast_cmd.finish(f"✅ 广播完成！成功 {success} 个群，失败 {fail} 个群。")
