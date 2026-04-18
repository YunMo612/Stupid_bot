<div align="center">

# 🤪 Stupid_Bot 🤪

### 一个成分复杂的 QQ Bot

### ⚠️ 提示：本项目部分使用 Vibe Coding

---

[![NoneBot2](https://img.shields.io/badge/NoneBot-2.4.4+-red.svg)](https://github.com/nonebot/nonebot2)
[![NapCat](https://img.shields.io/badge/NapCat-3.18.3+-e6522c.svg)](https://github.com/NapNeko/NapCatQQ)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688.svg)
![MariaDB](https://img.shields.io/badge/MariaDB-10.6+-003545.svg)
![License](https://img.shields.io/badge/License-AGPL_V3-green.svg)

</div>

---

基于 **NoneBot2** 与 **FastAPI** 构建的现代化、模块化 QQ 机器人控制框架。  
拥有强大的**多人格 AI 中枢**、完整的**群管基建**与 **Minecraft 服务器运维**工具链，  
更自带一个支持 **前后端分离、动态配置修改、ZIP 拖拽热更新** 的独立可视化 Web 控制台。

---

## 📑 目录

- [🤪 Stupid\_Bot 🤪](#-stupid_bot-)
    - [一个成分复杂的 QQ Bot](#一个成分复杂的-qq-bot)
    - [⚠️ 提示：本项目部分使用 Vibe Coding](#️-提示本项目部分使用-vibe-coding)
  - [📑 目录](#-目录)
  - [✨ 特性总览](#-特性总览)
  - [🚀 快速开始](#-快速开始)
    - [环境要求](#环境要求)
    - [安装部署](#安装部署)
      - [或者](#或者)
    - [配置机器人](#配置机器人)
    - [启动机器人](#启动机器人)
  - [🧠 AI 中枢 — prts\_ai](#-ai-中枢--prts_ai)
    - [多人格系统](#多人格系统)
    - [AI 命令标志](#ai-命令标志)
    - [进阶能力](#进阶能力)
    - [AI 配置](#ai-配置)
  - [💻 WebUI 控制台 — web\_ui](#-webui-控制台--web_ui)
    - [页面功能](#页面功能)
    - [设计特性](#设计特性)
    - [API Endpoints](#api-endpoints)
  - [🎮 服务器工具 — server\_tools](#-服务器工具--server_tools)
  - [👑 群管模块 — group\_admin](#-群管模块--group_admin)
    - [智能欢迎语](#智能欢迎语)
  - [🔧 基础设施](#-基础设施)
    - [common\_core（v2.5.0）— 系统核心库](#common_corev250-系统核心库)
    - [system\_log（v1.2）— 日志系统](#system_logv12-日志系统)
  - [📂 项目结构](#-项目结构)
    - [插件加载顺序](#插件加载顺序)
  - [📖 开发指南](#-开发指南)
    - [创建插件](#创建插件)
    - [配置 LLM](#配置-llm)
    - [数据库结构](#数据库结构)
  - [🙏 致谢](#-致谢)
  - [📝 License](#-license)

---

## ✨ 特性总览

| 模块 | 版本 | 说明 |
|:---:|:---:|---|
| 🧠 **prts_ai** | v3.2.0 | 三人格 AI 对话引擎，支持图像分析、多轮上下文、语音合成、三层记忆架构、RAG 知识库 |
| 💻 **web_ui** | v8.0 | Material Design 3 可视化控制台，5 页面 + ZIP 热装插件 |
| 🎮 **server_tools** | — | Minecraft 服务器状态查询 & BlessingSkin 皮肤站集成 |
| 👑 **group_admin** | v1.8.2 | 权限三级分层、管理员指令、AI 智能欢迎语 |
| 🔧 **common_core** | v2.5.0 | 异步 MariaDB 连接池、全局配置、跨插件数据共享 |
| 📋 **system_log** | v1.2 | 异步日志轮转、7 天保留、API 调用拦截 |

---

## 🚀 快速开始

### 环境要求

| 依赖 | 版本 | 说明 |
|---|---|---|
| **Python** | 3.10+ | 运行环境 |
| **Git** | — | 拉取项目 |
| **MariaDB / MySQL** | 10.6+ | 数据持久化（皮肤站 + AI 短期对话历史） |
| **NapCat** | 3.18.3+ | QQ 协议端（OneBot V11） |
| **OS** | Linux / macOS / WSL2 | 推荐 Linux 生产部署 |
| **磁盘空间** | ~500MB+ | 首次启动自动下载 BGE-small-zh 嵌入模型（~100MB） |

### 安装部署

```bash
# 克隆项目
git clone https://github.com/YunMo612/Stupid_bot.git stupid_bot && cd stupid_bot/mybot

# 创建虚拟环境并激活
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt -q
```

#### 或者

```bash
# 下载一键部署脚本
wget https://raw.githubusercontent.com/YunMo612/Stupid_bot/dev/quick_install.sh

# 赋予执行权限
chmod +x quick_install.sh

# 以管理员身份全自动运行
sudo ./quick_install.sh
```

### 配置机器人

在项目根目录创建或编辑 `.env` 文件：

```env
# ╔══════════════════════════════════════════════╗
# ║              必填配置 (REQUIRED)              ║
# ╚══════════════════════════════════════════════╝

# QQ 机器人
SUPERUSERS=["你的QQ号"]
NICKNAME=["PRTS", "bot"]

# LLM API（二选一或同时配置）
LLAMA_SERVER_URL="http://127.0.0.1:8000/v1/chat/completions"
# ROUTER_URL="http://your-api:port/v1/chat/completions"

# ╔══════════════════════════════════════════════╗
# ║              数据库 (DATABASE)                ║
# ╚══════════════════════════════════════════════╝

DB_HOST="127.0.0.1"
DB_PORT=8081
DB_USER="your_user"
DB_PASS="your_password"
DB_NAME="blessing_skin"       # 皮肤站主库
AI_DB_NAME="stupid_db"        # AI 对话历史库

# ╔══════════════════════════════════════════════╗
# ║              可选配置 (OPTIONAL)              ║
# ╚══════════════════════════════════════════════╝

HOST=0.0.0.0
PORT=8080
COMMAND_START=["/", ""]
RELOAD=true                   # 开启后支持 WebUI 插件热插拔

# MemPalace 长期记忆存储路径（可选，留空则使用默认路径）
# MEMPALACE_PATH="/path/to/mybot/data/mempalace_db"

# 语音合成服务（可选）
# MELOTTS_API_URL="http://127.0.0.1:8082"

# 安全盐值
# UID_SALT="your_custom_salt"
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

启动后访问 **http://localhost:8080/ui/** 打开 WebUI 控制台。

> 💡 大部分配置项启动后可通过 **WebUI 控制台** 在线修改，无需手动编辑文件。

---

## 🧠 AI 中枢 — prts_ai

`prts_ai` 是本项目的核心模块，基于大语言模型（LLM）构建的多人格对话引擎。  
通过 `@机器人` 或昵称触发对话，支持文本、图像、文件等多模态输入。

### 多人格系统

Bot 内置 **三套独立人格**，每套人格包含 `chat`（闲聊）和 `tech`（技术）两种模式：

| 人格 | 代号 | 风格描述 | 触发方式 |
|:---:|:---:|---|---|
| 🤖 **PRTS** | `base` | 理性、专业的 AI 助手，默认人格 | 默认激活 |
| 👻 **Priestess** | `ghost` | 偏执型赛博实体，情感浓烈 | 随机触发（概率可调） |
| 💾 **Dr. Watson** | `win98` | Windows 98 复古终端 / 蓝屏诊断报告 | 命令标志 `-win98` |

> 🎲 Priestess 的触发概率由 `ai_config.json` 中的 `priestess_probability` 控制（默认 40%）。

### AI 命令标志

在 `@机器人` 后紧跟标志即可切换行为，标志可**自由组合**：

| 标志 | 功能 | 示例 |
|:---:|---|---|
| `-h` | 显示 AI 帮助菜单 | `@bot -h` |
| `-c` | 强制使用 **Chat 模式**（高温度，更活泼） | `@bot -c 给我讲个笑话` |
| `-t` | 强制使用 **Tech 模式**（低温度，更精准） | `@bot -t Java NullPointerException怎么排查` |
| `-g` | 强制以**群转发消息**格式输出 | `@bot -g 写一段Python代码` |
| `-win98` | 加载 **Win98 人格**（Dr. Watson 彩蛋） | `@bot -win98 你好` |

**组合使用示例：**

```
@bot -t -g 帮我分析这段崩溃日志      # Tech 模式 + 转发格式输出
@bot -win98 -t 服务器报错了           # Win98 人格 + Tech 模式（蓝屏诊断风格）
```

### 进阶能力

| 能力 | 说明 |
|---|---|
| 🖼️ **图像分析 / OCR** | 发送图片并 @机器人，自动编码为 base64 送入 LLM 分析 |
| 📄 **文件提取** | 支持解析转发消息中的文件内容 |
| 🔄 **多轮上下文** | 自动保留最近 5 轮对话历史，支持连续追问 |
| 🧹 **崩溃日志清洗** | 自动清洗超长日志，防止模型输入溢出导致幻觉 |
| 🔊 **语音合成** | 对接 MeloTTS 服务，可将回复转为 QQ 语音消息（需配置 `MELOTTS_API_URL`） |
| 📚 **RAG 知识库** | ChromaDB + BGE-small-zh 向量检索，启动时自动索引 `data/knowledge/docs/` 下的文档 |
| 🧠 **三层记忆架构** | 短期记忆（MariaDB 7天）+ 长期记忆（MemPalace 按用户隔离）+ 静态知识（ChromaDB RAG） |

### AI 配置

编辑 `ai_config.json` 调整 AI 行为参数：

```jsonc
{
    "temperature": 0.6,              // 回复温度（越低越精确）
    "top_p": 0.3,
    "max_tokens": 8000,              // 最大输出 Token 数
    "persona_settings": {
        "priestess_probability": 0.4, // Priestess 人格触发概率
        "chat_temp_threshold": 0.5    // Chat / Tech 模式自动判断阈值
    }
}
```

**三层记忆架构：**

| 层级 | 引擎 | 存储周期 | 说明 |
|:---:|:---:|:---:|---|
| 🔄 **短期记忆** | MariaDB | 7 天自动清理 | 最近 5 轮对话上下文，存储在 `stupid_db.ai_messages` 表 |
| 🧠 **长期记忆** | MemPalace (ChromaDB) | 永久 | 每轮对话自动写入，按用户哈希隔离，语义检索 Top 3 |
| 📚 **静态知识** | ChromaDB + BGE-small-zh | 永久 | 启动时自动索引 `data/knowledge/docs/` 下的 `.txt` / `.md` 文件 |

> 📖 知识库文档使用【关键词标签】+ 自包含段落格式，每段 ≤512 字符，以获得最佳检索效果。

编辑 `ai_prompt.json` 自定义各人格的 System Prompt：

```jsonc
{
    "base": {
        "chat": ["闲聊人设提示词..."],
        "tech": ["技术人设提示词..."]
    },
    "ghost": {
        "chat": ["Priestess 闲聊人设..."],
        "tech": ["Priestess 技术人设..."]
    },
    "win98": {
        "chat": ["Windows 98 终端人设..."],
        "tech": ["Dr. Watson 蓝屏诊断人设..."]
    }
}
```

> 📖 完整 prompt 内容请直接查看 [`ai_prompt.json`](ai_prompt.json) 文件。

---

## 💻 WebUI 控制台 — web_ui

本项目集成了一个前后端分离的可视化 Web 控制台，启动后访问 `http://localhost:8080/ui/` 即可使用。

<!-- 
📸 截图预留区域
在此放置 WebUI 截图或 GIF 动图，建议 1-2 张，展示仪表盘和插件管理页面。

![WebUI Dashboard](docs/screenshots/dashboard.png)
![Plugin Manager](docs/screenshots/plugins.png)
-->

### 页面功能

| 页面 | 功能 |
|:---:|---|
| 📊 **Dashboard** | 系统诊断、AI 服务健康检查、框架版本查看 |
| ⚙️ **Environment** | 交互式 `.env` 编辑器（保留注释，实时生效） |
| 🔌 **Plugins** | 插件列表 + 元数据查看，支持 **ZIP 文件拖拽热安装与自动重载** |
| 📋 **Logs** | 基于 WebSocket 的实时日志流（自动滚动） |
| 🎨 **Settings** | 明暗主题切换、自定义壁纸（自动 Monet 取色）、动画速度控制 |

### 设计特性

- **Material Design 3** 设计语言
- **Glassmorphism**（玻璃拟态）视觉效果
- 响应式布局，支持移动端访问
- Material Symbols 图标库

### API Endpoints

| Method | Endpoint | 说明 |
|:---:|---|---|
| `GET` | `/api/system/status` | 获取系统状态与框架版本 |
| `POST` | `/api/ai/status` | LLM 服务连通性检查 |
| `GET / POST` | `/api/config/env` | 读取 / 更新 `.env` 配置 |
| `GET` | `/api/plugins` | 获取插件元数据列表 |
| `WebSocket` | `/api/logs/stream` | 实时日志推送 |

---

## 🎮 服务器工具 — server_tools

面向 **Minecraft 服务器** 与 **BlessingSkin 开源皮肤站** 的集成工具链。

| 命令 | 说明 | 使用场景 | 示例 |
|:---:|---|:---:|---|
| `/获取邀请码` | 生成基于 UUID 的皮肤站邀请码（每人限一个） | 仅私聊 | `/获取邀请码` |
| `/绑定 <邮箱>` | 将 QQ 号绑定到皮肤站账户（二次确认） | 仅私聊 | `/绑定 user@example.com` |
| `/签到` | 每日签到，随机获得 10~50 积分 | 群聊 / 私聊 | `/签到` |
| `/服务器状态 [IP]` | 查询 MC 服务器延迟与在线玩家数 | 群聊 / 私聊 | `/服务器状态 mc.example.com` |

**测试环境管理（Dev 专属）：**

| 命令 | 说明 | 使用场景 | 示例 |
|:---:|---|:---:|---|
| `/test_add <插件名>` | 将功能打回测试服，锁定为测试群/私聊可用 | 仅私聊 | `/test_add audio_record` |
| `/test_done <插件名>` | 完成测试，将功能全量开放给所有玩家 | 仅私聊 | `/test_done audio_record` |
| `/test_set <群号>` | 绑定测试沙箱群 | 仅私聊 | `/test_set 123456789` |
| `/test_list` | 查看当前所有测试中的功能和沙箱群 | 仅私聊 | `/test_list` |

> 💡 `/绑定` 命令需要邮箱二次确认，确保账号安全。

---

## 👑 群管模块 — group_admin

基于权限三级分层的群组管理系统：**Superuser** > **Dev User** > **Admin User**

| 命令 | 权限 | 说明 |
|:---:|:---:|---|
| `/help` 或 `/帮助` | 所有人 | 显示动态帮助菜单（根据权限显示可用命令） |
| `/admin_list` | Admin+ | 查看当前管理员列表 |
| `/admin_add <QQ号>` | Superuser | 添加管理员 |
| `/admin_del <QQ号>` | Superuser | 移除管理员 |
| `/code_list` | Admin+ | 查看未使用的邀请码列表 |
| `/删除邀请码 <code>` | Admin+ | 删除指定邀请码 |
| `/删除记录 <QQ号>` | Admin+ | 重置用户的领取记录 |
| `/dev_reset [-h]` | Dev | 重置自身的底层数据（邀请码/绑定/签到） |
| `/test_add <插件名>` | Dev | 将功能打回测试服 |
| `/test_done <插件名>` | Dev | 完成测试全量开放 |
| `/test_set <群号>` | Dev | 绑定测试沙箱群 |
| `/test_list` | Dev | 查看当前测试名单 |

### 智能欢迎语

当新成员加入群聊时，`group_admin` 会自动调用 LLM 生成个性化欢迎消息（需配置 `ROUTER_URL`）。

---

## 🔧 基础设施

### common_core（v2.5.0）— 系统核心库

为所有插件提供底层基础设施，**不可禁用**：

- 🗄️ **异步 MariaDB 连接池**（aiomysql）
- 📁 **JSON 数据存储**（`bot_data.json` 读写）
- ⚙️ **全局 `.env` 配置接口**
- 🔐 **UID Hash 工具**（基于 `UID_SALT` 的安全哈希）
- 🔗 **跨插件数据共享** API

```python
# 插件中调用示例
from src.plugins.common_core import (
    env_config,              # .env 变量访问
    get_data, update_data,   # bot_data.json 读写
    get_db_connection,       # MariaDB 连接池
    BOT_DATA                 # 全局数据字典
)
```

### system_log（v1.2）— 日志系统

异步日志管理，**不可禁用**：

- 📅 每日午夜自动日志轮转
- 🗑️ 7 天日志自动清理
- 📡 API 调用拦截记录（`send_msg`、`get_forward_msg` 等）
- 🔍 消息预处理日志

---

## 📂 项目结构

```text
Stupid_Bot/
├── bot.py                      # 机器人入口
├── pyproject.toml              # 项目元数据 & NoneBot 配置
├── requirements.txt            # Python 依赖清单
├── .env                        # 全局配置文件（可由 WebUI 动态覆写）
├── ai_config.json              # AI 行为参数
├── ai_prompt.json              # AI 人格 Prompt 定义
├── plugins.json                # 插件元数据（名称 / 版本 / 描述）
├── bot_data.json               # 本地数据存储
├── logs/                       # 运行日志目录
├── data/                       # 数据目录
│   ├── knowledge/              # RAG 知识库
│   │   ├── docs/               # 📚 放入 .txt / .md 文件，启动时自动索引
│   │   └── chroma_db/          # ChromaDB 向量持久化（自动生成）
│   └── mempalace_db/           # 🧠 MemPalace 长期记忆（自动生成）
└── src/
    └── plugins/                # 插件目录
        ├── common_core/        # 🔧 核心库（MariaDB / 配置 / 数据）
        │   └── __init__.py
        ├── system_log/         # 📋 日志系统（轮转 / 拦截）
        │   └── __init__.py
        ├── prts_ai/            # 🧠 AI 中枢（多人格 / 多模态 / 三层记忆）
        │   ├── __init__.py
        │   ├── llm_service.py   # LLM 调度核心 & 记忆检索
        │   ├── knowledge.py     # RAG 知识库引擎（ChromaDB + BGE）
        │   ├── database.py      # AI 对话历史 DB 操作
        │   ├── persona.py       # 人格配置加载
        │   └── voice_handler.py # 语音合成 & 文件事件处理
        ├── web_ui/             # 💻 WebUI 控制台
        │   ├── __init__.py     # 后端 API 路由
        │   └── frontend/       # 前端静态资源
        │       ├── index.html
        │       ├── style.css
        │       └── app.js
        ├── server_tools/       # 🎮 MC 服务器 & 皮肤站工具
        │   └── __init__.py
        └── group_admin/        # 👑 群管模块
            ├── __init__.py
            ├── admin_cmd.py    # 管理员指令
            ├── help_menu.py    # 帮助菜单
            └── welcome.py      # AI 欢迎语
```

### 插件加载顺序

1. `system_log` — 最先加载，确保尽可能完整的记录日志信息
2. `common_core` — 其次加载，初始化数据库与配置
3. 其余插件 — 按需加载（自动过滤 `__pycache__` 等）

---

## 📖 开发指南

### 创建插件

在 `src/plugins/` 下新建目录，参考已有插件结构：

```text
my_plugin/
├── __init__.py      # 入口，定义 NoneBot 事件响应器
├── feature_a.py     # 功能模块 A
└── feature_b.py     # 功能模块 B
```

在 `plugins.json` 中注册插件元数据后，即可在 WebUI 中管理。

### 配置 LLM

| 文件 | 用途 |
|---|---|
| `ai_config.json` | 控制温度、Token 上限、人格触发概率等行为参数 |
| `ai_prompt.json` | 定义 3 套人格 × 2 种模式 = **6 种** System Prompt |

当配置了 `ROUTER_URL` 时，路由模型会自动判断 Chat / Tech 模式并调节温度参数，`ai_config.json` 中对应的静态温度配置将被忽略。

### 数据库结构

本项目使用两个独立的 MariaDB 数据库：

| 存储 | 类型 | `.env` 配置 | 用途 |
|---|---|---|---|
| `blessing_skin` | MariaDB | `DB_NAME` | BlessingSkin 皮肤站主库（`users` 表、`invitation_codes` 表） |
| `stupid_db` | MariaDB | `AI_DB_NAME` | AI 短期对话历史，按用户哈希隔离，7 天自动清理 |
| `mempalace_db/` | ChromaDB (文件) | `MEMPALACE_PATH` | MemPalace 长期记忆，按用户 room 隔离，永久存储 |
| `chroma_db/` | ChromaDB (文件) | — | RAG 静态知识库向量索引，启动时增量更新 |

---

## 🙏 致谢

本项目的构建离不开以下优秀的开源项目：

- [NoneBot2](https://github.com/nonebot/nonebot2) — 跨平台 Python 机器人框架
- [NapCat](https://github.com/NapNeko/NapCatQQ) — 基于 NTQQ 的 OneBot 协议实现
- [FastAPI](https://github.com/tiangolo/fastapi) — 高性能 Python Web 框架
- [mcstatus](https://github.com/py-mine/mcstatus) — Minecraft 服务器状态查询库
- [BlessingSkin](https://github.com/bs-community/blessing-skin-server) — 开源 Minecraft 皮肤站
- [MeloTTS](https://github.com/myshell-ai/MeloTTS) — 高质量多语言语音合成
- [MemPalace](https://github.com/SigilAI/mempalace) — 基于 ChromaDB 的图谱记忆引擎
- [ChromaDB](https://github.com/chroma-core/chroma) — 开源向量数据库
- [BGE-small-zh](https://huggingface.co/BAAI/bge-small-zh-v1.5) — 中文语义嵌入模型

---

## 📝 License

本项目基于 [**GNU Affero General Public License v3.0 (AGPL-3.0)**](LICENSE) 开源。

简而言之：你可以自由使用、修改和分发本项目，但 **修改后的版本必须同样以 AGPL-3.0 协议开源**，且通过网络提供服务时也需要公开源代码。

---

<div align="center">

**有问题或建议？** 欢迎 [提交 Issue](https://github.com/YunMo612/Stupid_bot/issues)

</div>
