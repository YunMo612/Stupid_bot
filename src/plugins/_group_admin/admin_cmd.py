# ==============================================================================
# 管理员与开发者指令总成 (Admin Commands)
# ==============================================================================

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, GroupMessageEvent, Message
from nonebot.params import CommandArg

# 💡 神奇的魔法基建导入：直接拿来用，再也不用管繁琐的连接和文件锁了
from ..common_core import env_config, get_data, update_data, get_db_connection

# --- 权限校验辅助函数 ---
def check_permission(qq_id: str, require_dev: bool = False) -> bool:
    devs = set(get_data("dev_users", [])) | env_config.superusers
    if require_dev:
        return qq_id in devs
    admins = set(get_data("admin_users", []))
    return qq_id in (admins | devs)

# ==================== A. 数据库邀请码管理 ====================
delete_matcher = on_command("删除邀请码")
@delete_matcher.handle()
async def handle_delete_code(event: MessageEvent, args: Message = CommandArg()):
    if isinstance(event, GroupMessageEvent): await delete_matcher.finish("⚠️ 请在私聊中使用！")
    if not check_permission(str(event.get_user_id())): await delete_matcher.finish("❌ 权限不足！")
        
    target_code = args.extract_plain_text().strip()
    if not target_code: await delete_matcher.finish("⚠️ 请提供要删除的邀请码！")
        
    try:
        # 🌟 基建魔法：异步上下文，用完自动关
        async with get_db_connection() as conn:
            async with conn.cursor() as cursor:
                affected_rows = await cursor.execute("DELETE FROM invitation_codes WHERE code = %s", (target_code,))
        
        if affected_rows > 0: await delete_matcher.finish(f"✅ 已永久删除邀请码：\n{target_code}")
        else: await delete_matcher.finish("❓ 找不到该邀请码！可能已被使用。")
    except Exception as e:
        await delete_matcher.finish(f"🔴 数据库操作失败：{e}")


code_list_matcher = on_command("code_list", aliases={"查看邀请码"})
@code_list_matcher.handle()
async def handle_code_list(event: MessageEvent):
    if isinstance(event, GroupMessageEvent): await code_list_matcher.finish("⚠️ 请在私聊中使用！")
    if not check_permission(str(event.get_user_id())): await code_list_matcher.finish("❌ 权限不足！")
        
    try:
        async with get_db_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT code, generated_at FROM invitation_codes ORDER BY generated_at DESC")
                results = await cursor.fetchall()
                
        if not results: await code_list_matcher.finish("📭 当前数据库中没有未使用的邀请码。")
        
        msg_lines = [f"📜 当前可用邀请码 (共 {len(results)} 个)："]
        for row in results: msg_lines.append(f"🔑 {row[0]} ({row[1]})")
        await code_list_matcher.finish("\n".join(msg_lines))
    except Exception as e:
        await code_list_matcher.finish(f"🔴 数据库查询失败：{e}")


# ==================== B. JSON 本地数据管理 ====================
claimed_del_matcher = on_command("claimed_del", aliases={"删除记录"})
@claimed_del_matcher.handle()
async def handle_claimed_del(event: MessageEvent, args: Message = CommandArg()):
    if isinstance(event, GroupMessageEvent): await claimed_del_matcher.finish("⚠️ 请在私聊中使用！")
    if not check_permission(str(event.get_user_id())): await claimed_del_matcher.finish("❌ 权限不足！")
        
    target_qq = args.extract_plain_text().strip()
    if not target_qq: await claimed_del_matcher.finish("⚠️ 请提供要清除记录的QQ号！")
        
    # 🌟 基建魔法：安全地读取和更新数据
    claimed_users = get_data("claimed_users", [])
    if target_qq in claimed_users:
        claimed_users.remove(target_qq)
        update_data("claimed_users", claimed_users)
        await claimed_del_matcher.finish(f"✅ 成功清除 QQ {target_qq} 的领取记录！")
    else:
        await claimed_del_matcher.finish(f"❓ QQ {target_qq} 还没有领取过。")


admin_list_matcher = on_command("admin_list")
@admin_list_matcher.handle()
async def handle_admin_list(bot: Bot, event: MessageEvent):
    if isinstance(event, GroupMessageEvent): await admin_list_matcher.finish("⚠️ 请在私聊中使用！")
    if not check_permission(str(event.get_user_id())): await admin_list_matcher.finish("❌ 权限不足！")
        
    admin_users = set(get_data("admin_users", []))
    info_list = []
    for uid in admin_users:
        try:
            info = await bot.get_stranger_info(user_id=int(uid))
            info_list.append(f"🔸 {uid} ({info.get('nickname', '未知')})")
        except: info_list.append(f"🔸 {uid} (获取失败)")
    await admin_list_matcher.finish("👑 当前管理员列表：\n" + "\n".join(info_list))


admin_add_matcher = on_command("admin_add")
@admin_add_matcher.handle()
async def handle_admin_add(event: MessageEvent, args: Message = CommandArg()):
    if isinstance(event, GroupMessageEvent): await admin_add_matcher.finish("⚠️ 请在私聊中使用！")
    if not check_permission(str(event.get_user_id())): await admin_add_matcher.finish("❌ 权限不足！")
        
    new_admin = args.extract_plain_text().strip()
    admin_users = get_data("admin_users", [])
    if new_admin in admin_users: await admin_add_matcher.finish("✅ 该QQ已经是管理员。")
        
    admin_users.append(new_admin)
    update_data("admin_users", admin_users)
    await admin_add_matcher.finish(f"🎉 成功添加新管理员：{new_admin}")


admin_del_matcher = on_command("admin_del")
@admin_del_matcher.handle()
async def handle_admin_del(event: MessageEvent, args: Message = CommandArg()):
    if isinstance(event, GroupMessageEvent): await admin_del_matcher.finish("⚠️ 请在私聊中使用！")
    if not check_permission(str(event.get_user_id())): await admin_del_matcher.finish("❌ 权限不足！")
        
    del_admin = args.extract_plain_text().strip()
    if del_admin == str(event.get_user_id()): await admin_del_matcher.finish("❌ 警告：你不能删除自己！")
    if del_admin in env_config.superusers: await admin_del_matcher.finish("❌ 警告：不能删除最高权限开发者！")
        
    admin_users = get_data("admin_users", [])
    if del_admin not in admin_users: await admin_del_matcher.finish("❓ 该QQ不是管理员。")
        
    admin_users.remove(del_admin)
    update_data("admin_users", admin_users)
    await admin_del_matcher.finish(f"🗑️ 成功移除管理员：{del_admin}")


# ==================== C. 开发者强制重置 ====================
test_matcher = on_command("test", aliases={"fortest"})
@test_matcher.handle()
async def handle_test(event: MessageEvent, args: Message = CommandArg()):
    if isinstance(event, GroupMessageEvent): await test_matcher.finish("⚠️ 请在私聊中使用！")
    qq_id = str(event.get_user_id())
    # 强制校验：必须是 Dev 开发者才能使用
    if not check_permission(qq_id, require_dev=True): await test_matcher.finish("⛔ 权限不足！")

    arg_text = args.extract_plain_text().strip()
    if arg_text == "-h":
        await test_matcher.finish("🛠️ /test [无|-code|-band|-签到]")
    
    cleared = []
    
    if arg_text in ["", "-code"]:
        claimed = get_data("claimed_users", [])
        if qq_id in claimed:
            claimed.remove(qq_id)
            update_data("claimed_users", claimed)
            cleared.append("邀请码")
            
    if arg_text in ["", "-band"]:
        binds = get_data("bind_users", {})
        if qq_id in binds:
            del binds[qq_id]
            update_data("bind_users", binds)
            cleared.append("邮箱绑定")
            
    if arg_text in ["", "-签到"]:
        checks = get_data("checkin_records", {})
        if qq_id in checks:
            del checks[qq_id]
            update_data("checkin_records", checks)
            cleared.append("今日签到")

    if cleared: await test_matcher.finish(f"🛠️ 已重置你的限制：{', '.join(cleared)}")
    else: await test_matcher.finish("✨ 你的账号很干净，没有可清理的记录。")