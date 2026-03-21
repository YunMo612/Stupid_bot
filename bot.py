# ==============================================================================
# PRTS 机器人主启动入口 (bot.py)
# ==============================================================================

import nonebot
from nonebot.adapters.onebot.v11 import Adapter as ONEBOT_V11Adapter

# 1. 初始化 NoneBot (会自动读取根目录的 .env 文件)
nonebot.init()

# 2. 注册 OneBot V11 协议适配器 (与 QQ 互通的核心)
driver = nonebot.get_driver()
driver.register_adapter(ONEBOT_V11Adapter)

# 3. 挂载 FastAPI 实例 (为稍后的外部 API 接口做准备)
app = nonebot.get_asgi()

# 原来的自动扫描
nonebot.load_plugins("src/plugins")

# 🌟 强制召唤：逼迫框架加载大脑，如果敢报错就给我大声报出来！
# nonebot.load_plugin("src.plugins.prts_ai")

# (可选) 如果你以后安装了通过 pip 安装的第三方插件，可以使用这行：
# nonebot.load_from_toml("pyproject.toml")

if __name__ == "__main__":
    # 启动机器人！
    nonebot.run()
