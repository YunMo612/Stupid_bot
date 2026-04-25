# ==============================================================================
# 测试功能环境管理台 (Test Manager)
# 负责：控制插件的测试状态（仅 Dev/SuperUser 私聊可用）
# ==============================================================================

import os
import json
from nonebot import on_command, logger
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, GroupMessageEvent, Message
from nonebot.adapters import Event
from nonebot.message import run_preprocessor
from nonebot.matcher import Matcher
from nonebot.exception import IgnoredException
from nonebot.typing import T_State
from nonebot.params import CommandArg

from ..common_core.data_manager import get_data, update_data

# -------------------------------------------------------------------------
# 1. JSON 文件读写基建
# -------------------------------------------------------------------------
TEST_LIST_FILE = "test_list.json"

def load_test_list() -> dict:
    if not os.path.exists(TEST_LIST_FILE):
        return {"test_list": []}
    try:
        with open(TEST_LIST_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"读取 {TEST_LIST_FILE} 失败: {e}")
        return {"test_list": []}

def save_test_list(data: dict):
    try:
        with open(TEST_LIST_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.error(f"保存 {TEST_LIST_FILE} 失败: {e}")

# -------------------------------------------------------------------------
# 2. 权限校验辅助函数
# -------------------------------------------------------------------------
def check_dev_permission(qq_id: str) -> bool:
    devs = set(get_data("dev_users", []))
    return qq_id in devs


# -------------------------------------------------------------------------
# 3. 全局测试功能拦截器 (run_preprocessor)
# -------------------------------------------------------------------------
# 管理指令自身不拦截，防止递归锁死
_BYPASS_COMMANDS = {
    "test_done", "test_add", "test_again", "test_set", "test_list",
    "dev_reset", "fortest", "help", "帮助", "菜单",
}

# 管理类插件不拦截
_BYPASS_PLUGINS = {
    "server_tools", "group_admin", "system_log", "common_core", "web_ui",
}

@run_preprocessor
async def test_access_guard(matcher: Matcher, event: Event, state: T_State):
    """
    全局拦截器：按 test_list.json 控制未上线功能的访问权限。
    流程：插件在测试名单？ → 对应群聊/指令被限制？ → 是开发者？ → 放行/拦截
    """
    if not isinstance(event, MessageEvent):
        return

    # 获取 matcher 所属插件名（如 "prts_ai"、"server_tools"）
    plugin_name = matcher.plugin_name or ""
    if not plugin_name or plugin_name in _BYPASS_PLUGINS:
        return

    # 如果是命令类型，检查是否在白名单中
    command = state.get("_prefix", {}).get("command", ())
    if command and command[0] in _BYPASS_COMMANDS:
        return

    data = load_test_list()
    test_entries = data.get("test_list", [])
    if not test_entries:
        return

    for entry in test_entries:
        entry_plugin = entry.get("plugin_name", "")
        entry_commands = entry.get("commands", [])

        # Step 1：检查触发的插件是否在测试名单中
        if entry_plugin != plugin_name:
            continue

        # Step 2：如果有具体命令列表且触发的是命令，检查是否被限制
        # commands 为空 → 整个插件受限；不为空 → 仅列出的命令受限
        if entry_commands and command:
            cmd_str = command[0]
            # 兼容 JSON 中带 / 前缀的命令名（如 "/record" → "record"）
            normalized = {c.lstrip("/") for c in entry_commands}
            if cmd_str not in normalized:
                continue  # 此命令不在限制范围 → 放行

        # Step 3：开发者放行
        if check_dev_permission(str(event.get_user_id())):
            return

        # Step 4：测试群放行 —— 如果消息来自测试沙箱群，允许触发
        test_group = get_data("test_group")
        if test_group and isinstance(event, GroupMessageEvent):
            if str(event.group_id) == str(test_group):
                return

        # 非开发者、非测试群 → 拦截并提示（同一事件只提示一次）
        display_name = entry.get("nickname") or entry_plugin
        if not getattr(event, "_test_guard_notified", False):
            event._test_guard_notified = True
            await matcher.send(f"🔒 功能 [{display_name}] 仍在测试阶段，暂未对外开放。")
        raise IgnoredException(f"测试功能拦截: {plugin_name}")


# ==============================================================================
# 🌟 指令 1：/test_done {插件名} [指令] - 完成测试并开放
# ==============================================================================
test_done = on_command("test_done", priority=1, block=True)

@test_done.handle()
async def handle_test_done(event: MessageEvent, args: Message = CommandArg()):
    if isinstance(event, GroupMessageEvent): await test_done.finish("⚠️ 请在私聊中使用！")
    if not check_dev_permission(str(event.get_user_id())): await test_done.finish("⛔ 权限不足！")

    raw = args.extract_plain_text().strip()
    if not raw:
        await test_done.finish(
            "⚠️ 用法：\n"
            "/test_done {插件名}        — 整个插件全量开放\n"
            "/test_done {插件名} {指令}  — 仅开放该插件下的某条指令\n"
            "示例：/test_done audio_record /record"
        )

    parts = raw.split(None, 1)
    target_plugin = parts[0]
    target_cmd = parts[1].strip() if len(parts) > 1 else None

    data = load_test_list()
    test_list = data.get("test_list", [])

    # 按 plugin_name 或 nickname 定位条目
    found_idx = -1
    for i, item in enumerate(test_list):
        if target_plugin in (item.get("plugin_name"), item.get("nickname")):
            found_idx = i
            break

    if found_idx == -1:
        await test_done.finish(f"❓ 未在测试库中找到 [{target_plugin}]，请检查输入。")

    entry = test_list[found_idx]
    plugin_name = entry.get("plugin_name")

    if target_cmd:
        # 仅开放某条指令：从 commands 列表中移除
        cmds = entry.get("commands", [])
        normalized_cmd = target_cmd.lstrip("/")
        removed = [c for c in cmds if c.lstrip("/") == normalized_cmd]
        if not removed:
            await test_done.finish(f"❓ 插件 [{plugin_name}] 的受限指令中没有 [{target_cmd}]。\n当前受限指令：{', '.join(cmds) or '(整体受限)'}")
        entry["commands"] = [c for c in cmds if c.lstrip("/") != normalized_cmd]
        # 如果 commands 清空了，整个条目也没意义了，一并移除
        if not entry["commands"]:
            test_list.pop(found_idx)
            save_test_list(data)
            await test_done.finish(f"✅ 已开放指令 [{target_cmd}]，且 [{plugin_name}] 已无其他受限指令，已整体移出测试名单。")
        save_test_list(data)
        await test_done.finish(f"✅ 已开放指令 [{target_cmd}]！\n插件 [{plugin_name}] 仍有 {len(entry['commands'])} 条指令在测试中。")
    else:
        # 整个插件全量开放
        test_list.pop(found_idx)
        save_test_list(data)
        await test_done.finish(f"✅ 审批通过：已将 [{plugin_name}] 移出测试名单！\n该功能现已对所有玩家全量开放。")


# ==============================================================================
# 🌟 指令 2：/test_add {插件名} [-n 昵称] [指令1 指令2 ...] - 将功能打回测试服
# ==============================================================================
test_add = on_command("test_add", aliases={"test_again"}, priority=1, block=True)

@test_add.handle()
async def handle_test_add(event: MessageEvent, args: Message = CommandArg()):
    if isinstance(event, GroupMessageEvent): await test_add.finish("⚠️ 请在私聊中使用！")
    if not check_dev_permission(str(event.get_user_id())): await test_add.finish("⛔ 权限不足！")

    raw = args.extract_plain_text().strip()
    if not raw:
        await test_add.finish(
            "⚠️ 用法：\n"
            "/test_add {插件名}                     — 锁定整个插件\n"
            "/test_add {插件名} -n {昵称}            — 锁定并设置昵称\n"
            "/test_add {插件名} /cmd1 /cmd2          — 仅锁定特定指令\n"
            "/test_add {插件名} -n {昵称} /cmd1 /cmd2\n"
            "示例：/test_add audio_record -n 音频录制 /record /stop"
        )

    # 解析参数
    tokens = raw.split()
    target_plugin = tokens[0]
    nickname = None
    commands = []

    i = 1
    while i < len(tokens):
        if tokens[i] == "-n" and i + 1 < len(tokens):
            nickname = tokens[i + 1]
            i += 2
        else:
            commands.append(tokens[i])
            i += 1

    data = load_test_list()
    test_list = data.get("test_list", [])

    # 检查是否已存在 → 追加模式
    existing = None
    for item in test_list:
        if target_plugin == item.get("plugin_name"):
            existing = item
            break

    if existing:
        if not commands:
            await test_add.finish(f"⚠️ 插件 [{target_plugin}] 已在测试名单中。\n如需追加指令，请附带具体指令名。\n示例：/test_add {target_plugin} /new_cmd")
        # 追加新指令到已有条目
        old_cmds = set(existing.get("commands", []))
        new_cmds = [c for c in commands if c not in old_cmds]
        if not new_cmds:
            await test_add.finish(f"⚠️ 这些指令已存在于 [{target_plugin}] 的测试名单中，无需重复添加。")
        existing["commands"] = list(old_cmds | set(new_cmds))
        if nickname:
            existing["nickname"] = nickname
        save_test_list(data)
        await test_add.finish(
            f"🛠️ 已向 [{target_plugin}] 追加 {len(new_cmds)} 条受限指令：{', '.join(new_cmds)}\n"
            f"当前受限指令总数：{len(existing['commands'])}"
        )
    else:
        # 新建条目
        next_num = max([item.get("number", 0) for item in test_list] + [0]) + 1
        new_entry = {
            "number": next_num,
            "plugin_name": target_plugin,
            "nickname": nickname or target_plugin,
            "commands": commands
        }
        test_list.append(new_entry)
        save_test_list(data)

        scope = f"受限指令：{', '.join(commands)}" if commands else "范围：整个插件"
        await test_add.finish(
            f"🛠️ 已将 [{target_plugin}] 加入测试名单！\n"
            f"昵称：{new_entry['nickname']}\n"
            f"{scope}"
        )


# ==============================================================================
# 🌟 指令 3：/test_set {群号} - 绑定测试沙箱群
# ==============================================================================
test_set = on_command("test_set", priority=1, block=True)

@test_set.handle()
async def handle_test_set(event: MessageEvent, args: Message = CommandArg()):
    if isinstance(event, GroupMessageEvent): await test_set.finish("⚠️ 请在私聊中使用！")
    if not check_dev_permission(str(event.get_user_id())): await test_set.finish("⛔ 权限不足！")

    group_id_str = args.extract_plain_text().strip()
    
    if not group_id_str.isdigit():
        await test_set.finish("⚠️ 群号格式错误，必须是纯数字！")
        
    group_id = int(group_id_str)
    
    update_data("test_group", group_id)
    
    await test_set.finish(f"🎯 环境挂载成功：已将测试沙箱群设定为 [群: {group_id}]！\n所有处于测试名单内的功能，现在将只对该群生效。")


# ==============================================================================
# 🌟 指令 4：/test_list - 查看当前所有测试中的功能
# ==============================================================================
test_list_cmd = on_command("test_list", priority=1, block=True)

@test_list_cmd.handle()
async def handle_test_list(event: MessageEvent):
    if isinstance(event, GroupMessageEvent): await test_list_cmd.finish("⚠️ 请在私聊中使用！")
    if not check_dev_permission(str(event.get_user_id())): await test_list_cmd.finish("⛔ 权限不足！")

    data = load_test_list()
    test_list = data.get("test_list", [])
    
    if not test_list:
        msg = "📭 当前没有正在测试中的功能，所有插件均已全量开放。"
    else:
        msg = f"🧪 【当前沙箱测试名单】({len(test_list)} 项)\n" + "-" * 25 + "\n"
        for item in test_list:
            num = item.get("number", "?")
            name = item.get("plugin_name", "未知")
            nick = item.get("nickname", "")
            cmds = item.get("commands", [])
            
            label = f"{name} ({nick})" if nick and nick != name else name
            scope = "、".join(cmds) if cmds else "🔒 整个插件受限"
            
            msg += f"#{num} 📦 {label}\n"
            msg += f"   🔑 {scope}\n"
            msg += "-" * 25 + "\n"
            
    # 追加当前测试群状态
    test_group = get_data("test_group")
    if test_group:
        msg += f"\n🎯 当前沙箱群: {test_group}"
    else:
        msg += "\n⚠️ 尚未绑定测试沙箱群 (请使用 /test_set 设置)"
        
    await test_list_cmd.finish(msg.strip())