# ==============================================================================
# 统一数据库连接中心 (Database Manager)
# 负责：提供 MariaDB 的异步连接上下文，自动处理配置读取与连接关闭
# ==============================================================================

import aiomysql
from contextlib import asynccontextmanager
from nonebot import logger

# 导入我们在 config.py 里写好的全局配置
from .config import env_config

@asynccontextmanager
async def get_db_connection():
    """
    安全的异步数据库连接上下文管理器。
    
    使用示例:
        from src.plugins.common_core import get_db_connection
        
        async with get_db_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT * FROM users")
                result = await cursor.fetchall()
    """
    conn = None
    try:
        # 这里的参数全部从 .env 环境变量里动态读取
        conn = await aiomysql.connect(
            host=env_config.db_host,
            port=env_config.db_port,
            user=env_config.db_user,
            password=env_config.db_pass,
            db=env_config.db_name,
            autocommit=True
        )
        yield conn  # 把连接借给调用的业务模块
        
    except Exception as e:
        logger.error(f"🔴 数据库底层连接异常！请检查 .env 配置或 MariaDB 服务。详细原因: {e}")
        raise e
    
    finally:
        # 业务模块用完后（或者发生报错后），无论如何都会执行这里，安全断开连接
        if conn:
            conn.close()