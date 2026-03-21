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
        "🤖 欢迎使用服务器综合助手！\n\n"
        "【常规指令】\n"
        "1. /获取邀请码 (限私聊)\n"
        "2. /服务器状态 (查延迟人数)\n"
        "3. /绑定 邮箱 (绑定皮肤站账号)\n"
        "4. /签到 (每天领积分)\n"
        "5. /ai 问题或图片 (和 AI 聊天)\n"
        "6. /help"
    )
    
    admin_msg = (
        "\n\n【🛡️ 腐竹/管理指令 (限私聊)】\n"
        "7. /code_list (查看可用邀请码)\n"
        "8. /删除邀请码 密钥\n"
        "9. /删除记录 QQ号 (重置某人领取资格)\n"
        "10. /admin_list (查看所有管理)\n"
        "11. /admin_add QQ号\n"
        "12. /admin_del QQ号"
    )
    
    dev_msg = (
        "\n\n【⚙️ Dev 开发者指令】\n"
        "13. /test [-h] (底层数据重置)"
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