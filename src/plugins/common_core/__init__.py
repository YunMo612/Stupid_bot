# ==============================================================================
# Common Core 模块入口 (__init__.py)
# 负责：将本模块内的核心配置、数据管理等接口暴露给其他插件使用
# ==============================================================================

from nonebot.plugin import PluginMetadata

# 1. 定义插件元数据（让 NoneBot 框架和控制台能识别这个模块）
__plugin_meta__ = PluginMetadata(
    name="公共核心基建 (Common Core)",
    description="提供全局环境变量配置、本地数据 JSON 读写与数据库连接池等基础服务。",
    usage="本模块为底层驱动，仅供其他模块内部跨文件调用，不直接响应任何用户的 QQ 指令。",
    type="library", # 标记为核心库
)

# 2. 统一导出内部的类和函数
# 这样其他模块就可以写: from src.plugins.common_core import env_config, get_data
from .config import env_config
from .data_manager import get_data, update_data, BOT_DATA

# 3. 预留数据库导出接口 (等我们稍后写完 database.py 再解除注释)
from .database import get_db_connection