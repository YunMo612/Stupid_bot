# <center>🤪 Stupid_Bot 🤪
#### <center>一个成分复杂的QQbot
<center> ⚠️使用Vibe Coding⚠️ </center>

---

[![NoneBot2](https://img.shields.io/badge/NoneBot-2.0.0+-red.svg)](https://github.com/nonebot/nonebot2)
[![NapCat](https://img.shields.io/badge/Napcat-3.18.3+-e6522c.svg)](https://github.com/NapNeko/NapCatQQ)
[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

---

基于 **NoneBot2** 与 **FastAPI** 构建的现代化、模块化 QQ 机器人控制框架。不仅拥有强大的 AI 中枢与群管基建，更自带一个支持**前后端分离、动态配置修改、ZIP 拖拽热更新**的独立可视化 Web 控制台。

---
 - [ ] FastAPI
 - [ ] WebUI完善

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

## 🚀 部署指南 (Quick Start)

### 1. 环境准备
请确保你的服务器或本地电脑已安装以下环境：
* **Python 3.9** 或更高版本
* **Git** (用于拉取代码)

### 2. 克隆项目与安装依赖
首先，将本项目克隆到你的本地/服务器中：
```bash
git clone [https://github.com/你的用户名/Stupid_bot.git](https://github.com/你的用户名/Stupid_bot.git)
cd Stupid_bot
```

### 3.创建虚拟环境
```bash
python -m venv .venv
```
#### 激活虚拟环境 (Linux / macOS)
```bash
source .venv/bin/activate
```
#### 激活虚拟环境 (Windows CMD)
```bash
.venv\Scripts\activate
```
### 4.安装 NoneBot2 运行所需的所有依赖
```bash
pip install -r requirements.txt
```
### 环境配置 (.env)

#### 在项目根目录创建或修改 .env 文件。以下是基础配置模板：
```text
HOST=0.0.0.0
PORT=8080
SUPERUSERS=["你的QQ号"]
NICKNAME=["PRTS", "bot"]
COMMAND_START=["/", ""]

# 大模型 API 路由配置 (可直接在 WebUI 中动态修改)
LLAMA_SERVER_URL="http://你的大模型IP:端口/v1/chat/completions"
ROUTER_URL="http://你的路由IP:端口/v1/chat/completions"

# 开启热重载 (重要：WebUI 的插件热插拔及拖拽安装极度依赖此项配置)
RELOAD=true
```

