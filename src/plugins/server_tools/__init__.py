# ==============================================================================
# MC 服务器工具模块入口 (__init__.py)
# ==============================================================================

from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="服务器工具 (Server Tools)",
    description="处理皮肤站邀请码、账号绑定、每日签到积分以及查询服务器在线状态。",
    usage="提供 /获取邀请码, /绑定, /签到, /服务器状态 等指令。",
    type="application",
)

# 自动导入并激活当前目录下的所有业务模块
from . import invite
from . import bind_sign
from . import query