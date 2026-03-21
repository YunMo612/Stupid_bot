# ==============================================================================
# 系统日志持久化模块 (System Log)
# 负责：将控制台的实时日志按天分文件夹同步写入本地文件，生命周期 7 天
# ==============================================================================

import os
from nonebot.log import logger
from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="系统日志持久化 (System Log)",
    description="自动将 NoneBot 运行日志按天分文件夹写入，保留 7 天。",
    usage="后台自动运行，无需手动干预。",
    type="library",
)

# 基础日志目录
LOG_DIR = "logs"

# 🌟 核心魔法：向 NoneBot 底层的 loguru 添加文件输出管道
logger.add(
    # 路径中加入 {time:YYYY-MM-DD} 作为文件夹层级
    # loguru 会自动识别，如果今天文件夹不存在，它会自动帮你建一个！
    # 最终文件路径类似于：logs/2026-03-21/prts_run_16-30-05.log
    os.path.join(LOG_DIR, "{time:YYYY-MM-DD}", "prts_run_{time:HH-mm-ss}.log"), 
    
    rotation="5 MB",            # 单次运行时间过长，满 5MB 依然会自动切割防爆裂
    retention="7 days",         # 🌟 核心修改：缩短生命周期，只保留最近 7 天的日志
    level="INFO",               
    encoding="utf-8",           
    enqueue=True,               
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{module}:{line} - {message}"
)

logger.success("📁 [基建] 实时日志持久化已挂载 (按天分拣 & 7天轮转模式)！")