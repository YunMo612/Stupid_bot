# <center>🤪 Stupid_Bot 🤪
### <center>一个成分复杂的QQbot
### <center> ⚠️提示：本项目部分使用Vibe Coding </center>

---

[![NoneBot2](https://img.shields.io/badge/NoneBot-2.0.0+-red.svg)](https://github.com/nonebot/nonebot2)
[![NapCat](https://img.shields.io/badge/Napcat-3.18.3+-e6522c.svg)](https://github.com/NapNeko/NapCatQQ)
[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

---

基于 **NoneBot2** 与 **FastAPI** 构建的现代化、模块化 QQ 机器人控制框架。不仅拥有强大的 AI 中枢与群管基建，更自带一个支持**前后端分离、动态配置修改、ZIP 拖拽热更新**的独立可视化 Web 控制台。

---

## 🚀 快速开始

### 环境要求

- **Python 3.9+**
- **Git**
- **Linux/macOS** 或 Windows（推荐 WSL2）

### 一键启动

```bash
# 克隆项目
git clone https://github.com/YunMo612/Stupid_bot.git stupid_bot && cd stupid_bot/mybot

# 创建虚拟环境并激活
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt -q
```

### 配置机器人

在项目根目录创建或编辑 `.env` 文件，填写以下**必填项**：

```env
# === 必填：QQ 机器人配置 ===
SUPERUSERS=["你的QQ号"]
NICKNAME=["PRTS", "bot"]

# === 必填：LLM API 配置 ===
# 二选一：本地 Llama 或自建 API 路由
LLAMA_SERVER_URL="http://127.0.0.1:8000/v1/chat/completions"
# ROUTER_URL="http://your-api:port/v1/chat/completions"

# === 可选 ===
HOST=0.0.0.0
PORT=8080
COMMAND_START=["/", ""]
RELOAD=true  # 开启后支持 WebUI 插件热插拔
```

### 启动机器人

```bash
# 前台运行
nb run --reload

# 后台运行（使用 screen）
screen -S bot
source .venv/bin/activate
nb run --reload
# 按 Ctrl+A+D 挂起窗口
```

访问 `http://localhost:8080` 打开 WebUI 控制台

💡 其余配置项启动后可通过 **WebUI 控制台** 动态修改。

---

## ✨ 核心特性 (Features)

* **💻 现代化 WebUI 控制台**：自带赛博暗黑风/日间模式丝滑切换的网页仪表盘，数据通过 API 实时双向绑定。
* **🔌 模块热插拔系统**：无需重启机器，在网页端一键启用/禁用插件；支持直接将 `.zip` 插件包拖入网页实现热安装与自动重载。
* **🧠 LLM 核心大脑**：内置 `prts_ai` 模块，支持对接本地大模型（如 Llama）或自建 API 路由，包含多重人设与记忆上下文管理。
* **📝 神经日志管道**：自动按天分文件夹（`logs/YYYY-MM-DD`）管理日志，支持自动轮转与清理，网页端实时流式渲染（带终端级颜色高亮）。
* **🛠️ 实用群管与工具**：包含账号绑定、每日签到、积分系统等基础数据交互功能。

---

## 📂 项目结构 (Directory Structure)

```text
Stupid_Bot/
├── bot.py                  # 机器人主启动入口
├── .env                    # 全局配置文件 (可由 WebUI 动态覆写)
├── requirements.txt        # Python 依赖清单
├── logs/                   # 系统运行日志目录 (自动生成)
└── src/
    └── plugins/            # 核心插件目录
        ├── common_core/    # 基础核心库 (数据库操作、JSON持久化)
        ├── group_admin/    # 群管模块 (进群欢迎、基础指令)
        ├── prts_ai/        # AI 中枢大脑 (大模型请求调度)
        ├── server_tools/   # 玩家工具 (皮肤站绑定、签到系统)
        ├── system_log/     # 日志基建 (按天轮转与持久化)
        └── web_ui/         # 可视化监控前端与 API 后端
            ├── __init__.py # 核心 API 路由与后端逻辑
            └── frontend/   # 前后端分离的纯静态资源
                ├── index.html
                ├── style.css
                └── app.js
```

## 📖 开发指南

### 创建插件

在 `src/plugins/` 下新建插件目录，参考 `group_admin/` 结构即可。

### 配置 LLM

编辑 `ai_config.json` 和 `ai_prompt.json` 自定义 AI 人设与行为。

### 使用 WebUI

启动后访问 `http://localhost:8080`（默认），可视化管理插件、查看日志、修改配置。

## 常见命令

```bash
# 查看 NoneBot 帮助
nb -h

# 查看实时日志
tail -f logs/$(date +%Y-%m-%d)/*.log

# 安装特定插件
nb plugin install <插件名>
```

## 📝 License

MIT License - 自由使用与修改

---

**有问题？** 欢迎提交 Issue

