# ==============================================================================
# 动态帮助菜单 (Help Menu)
# ==============================================================================

from nonebot import on_command
from nonebot.rule import to_me
from nonebot.adapters.onebot.v11 import MessageEvent, GroupMessageEvent

# 💡 从核心基建借用数据读取功能
from ..common_core import get_data, env_config

help_matcher = on_command("help", rule=to_me(), aliases={"帮助", "菜单"})

@help_matcher.handle()
async def handle_help(event: MessageEvent):
    base_msg = (
        "🤖 【服务器综合助手 · 指令手册】\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📌 常规指令\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "/获取邀请码      — 领取皮肤站注册码 (限私聊)\n"
        "/绑定 <邮箱>     — 绑定皮肤站账号 (限私聊)\n"
        "/签到            — 每日签到领积分\n"
        "/服务器状态 [IP]  — 查询 MC 服务器延迟与在线人数\n"
        "@机器人 <问题>   — 和 AI 聊天 (支持图片/文件)\n"
        "/help            — 查看本帮助\n"
        "\n"
        "💡 AI 支持标志组合：-h(帮助) -c(闲聊) -t(技术) -g(转发) -win98(彩蛋)"
    )
    
    admin_msg = (
        "\n\n━━━━━━━━━━━━━━━━━━━━\n"
        "🛡️ 管理员指令 (限私聊)\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "/code_list             — 查看可用邀请码\n"
        "/删除邀请码 <密钥>      — 删除指定邀请码\n"
        "/删除记录 <QQ号>        — 重置某人的领取资格\n"
        "/admin_list            — 查看管理员列表\n"
        "/admin_add <QQ号>      — 添加管理员\n"
        "/admin_del <QQ号>      — 移除管理员\n"
        "/广播 <消息> [-群号] [-不匿名]  — 群发广播"
    )
    
    dev_msg = (
        "\n\n━━━━━━━━━━━━━━━━━━━━\n"
        "⚙️ 开发者指令 (限私聊)\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "/dev_reset [-h]        — 重置自身底层数据\n"
        "/test_add <插件> [-n 昵称] [/cmd ...]  — 加入测试名单\n"
        "/test_done <插件> [/cmd]               — 开放测试功能\n"
        "/test_set <群号>       — 绑定测试沙箱群\n"
        "/test_list             — 查看测试名单"
    )
    
    qq_id = str(event.get_user_id())
    is_private = not isinstance(event, GroupMessageEvent)
    
    # 获取实时权限名单
    admins = set(get_data("admin_users", []))
    devs = set(get_data("dev_users", [])) | env_config.superusers
    
    final_msg = base_msg
    
    # 只有私聊时，才展示高级菜单
    if is_private:
        if qq_id in (admins | devs):
            final_msg += admin_msg
        if qq_id in devs:
            final_msg += dev_msg
            
    await help_matcher.finish(final_msg)