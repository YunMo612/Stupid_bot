# ==============================================================================
# 数据库操作模块 (Database) - 独立架构、全自动化版
# ==============================================================================
import hashlib
import aiomysql
from nonebot import logger, get_driver

# 获取 NoneBot 的全局配置对象
env_config = get_driver().config

# 🌟 从 .env 环境变量动态读取配置
SECRET_SALT = getattr(env_config, "uid_salt", "PRTS_SECRET_!@#")
DB_HOST = getattr(env_config, "db_host", "127.0.0.1")
DB_PORT = int(getattr(env_config, "db_port", 3306))
DB_USER = getattr(env_config, "db_user", "root")
DB_PASS = getattr(env_config, "db_pass", "")

# 🌟 专属 AI 数据库名，与其他模块（如 blessing_skin）物理隔离
AI_DB_NAME = getattr(env_config, "ai_db_name", "stupid_db") 

# 全局数据库连接池
_db_pool = None

async def init_tables_and_events():
    """自动化初始化：开机检查/创建核心双表与自动净化机制"""
    if not _db_pool:
        return

    # 1. users 表 (负责账户与积分体系)
    sql_create_users = """
        CREATE TABLE IF NOT EXISTS users (
            uid VARCHAR(64) PRIMARY KEY,
            nickname VARCHAR(100),
            score INT DEFAULT 0,
            last_sign_at DATETIME
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """

    # 2. ai_messages 表 (负责 LLM 上下文隔离，含双索引)
    sql_create_ai_messages = """
        CREATE TABLE IF NOT EXISTS ai_messages (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            uid VARCHAR(64) NOT NULL,
            role VARCHAR(20) NOT NULL,
            content TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_uid (uid),
            INDEX idx_created_at (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """

    # 3. 自动净化机制 (MariaDB Event: 清理 7 天前上下文数据)
    sql_create_event = """
        CREATE EVENT IF NOT EXISTS auto_clean_ai_messages
        ON SCHEDULE EVERY 1 DAY
        DO
        DELETE FROM ai_messages WHERE created_at < NOW() - INTERVAL 7 DAY;
    """

    async with _db_pool.acquire() as conn:
        async with conn.cursor() as cur:
            try:
                # 执行建表
                await cur.execute(sql_create_users)
                await cur.execute(sql_create_ai_messages)
                logger.success(f"✅ [MySQL] AI 核心数据表 (users, ai_messages) 初始化完成于库: {AI_DB_NAME}")
                
                # 尝试开启事件调度器并挂载自动清理事件
                try:
                    await cur.execute("SET GLOBAL event_scheduler = ON;")
                    await cur.execute(sql_create_event)
                    logger.success("✅ [MySQL] 自动净化机制 (7天过期清理) 部署完成！")
                except Exception as e:
                    logger.warning(f"⚠️ [MySQL] 定时事件部署受限(可能需 root 权限)。请在 Navicat 中手动执行 SET GLOBAL event_scheduler = ON; 报错: {e}")
            except Exception as e:
                logger.error(f"❌ [MySQL] AI 数据库自动化初始化失败: {e}")

async def init_db_pool():
    """初始化全局数据库连接池 (在 NoneBot 启动时调用)"""
    global _db_pool
    try:
        _db_pool = await aiomysql.create_pool(
            host=DB_HOST, 
            port=DB_PORT,
            user=DB_USER, 
            password=DB_PASS,
            db=AI_DB_NAME,  # 强制连接独立的 AI_DB_NAME
            charset='utf8mb4', 
            autocommit=True,
            minsize=1, 
            maxsize=10
        )
        logger.success(f"✅ [MySQL] AI 专属数据库连接池初始化成功！({DB_HOST}:{DB_PORT} - {AI_DB_NAME})")
        
        # 连接池建立后，立即执行自动化建表与任务挂载
        await init_tables_and_events()
        
    except Exception as e:
        logger.error(f"❌ [MySQL] 数据库连接池初始化失败: {e}")

async def close_db_pool():
    """关闭数据库连接池 (在 NoneBot 关闭时调用)"""
    global _db_pool
    if _db_pool is not None:
        _db_pool.close()
        await _db_pool.wait_closed()
        logger.info("🛑 [MySQL] 数据库连接池已安全断开。")

def get_hashed_uid(qq_id: str) -> str:
    """对 QQ 号进行加盐哈希，落实隐私安全与上下文隔离"""
    raw_str = f"{qq_id}_{SECRET_SALT}"
    return hashlib.sha256(raw_str.encode('utf-8')).hexdigest()

async def fetch_chat_history_from_db(hashed_uid: str, limit: int = 5) -> list:
    """从数据库拉取短期上下文记忆"""
    if not _db_pool:
        return []
        
    query = """
        SELECT role, content FROM ai_messages 
        WHERE uid = %s 
        ORDER BY created_at DESC LIMIT %s
    """
    history = []
    async with _db_pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(query, (hashed_uid, limit * 2))
            rows = await cur.fetchall()
            for row in reversed(rows):
                history.append({"role": row["role"], "content": row["content"]})
    return history

async def save_message_to_db(hashed_uid: str, role: str, content: str):
    """将玩家提问或 AI 回复存入数据库，仅作为记录账本"""
    if not _db_pool:
        return
        
    query = "INSERT INTO ai_messages (uid, role, content) VALUES (%s, %s, %s)"
    async with _db_pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(query, (hashed_uid, role, content))

async def clear_memory_in_db(hashed_uid: str):
    """清除特定用户的数据库对话上下文"""
    if not _db_pool:
        return
        
    query = "DELETE FROM ai_messages WHERE uid = %s"
    async with _db_pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(query, (hashed_uid,))