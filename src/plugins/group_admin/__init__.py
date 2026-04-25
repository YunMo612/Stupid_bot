# ==============================================================================
# 群管与控制台模块入口 (__init__.py)
# ==============================================================================

from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="群管与后台模块 (Group Admin)",
    description="处理入群欢迎、管理员指令、开发者测试及帮助菜单。",
    usage="直接加载运行，提供 /help, /admin_list 等指令。",
    type="application",
)

# 自动导入并激活当前目录下的所有子模块
from . import help_menu
from . import welcome
from . import admin_cmd
from . import broadcast