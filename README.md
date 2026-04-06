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

## ✨ 特性与功能(Features)

* **💻 高度现代化的 WebUI 控制台**：本项目集成了网页仪表盘，用户可直接在webui中快速修改本项目的全局变量和配置文件。
* **🔌 模块化功能插件**：本项目支持直接将 `.zip` 插件包拖入网页实现热安装与自动重载。
* **🧠 大语言模型支持**：内置 `stupid_ai` 模块，支持对接人工智能大语言模型（如 Llama）或自建 API 路由，包含多重人设与记忆上下文管理。
* **🛠️ 实用群管与工具**：包含账号绑定、每日签到、积分系统等基础数据交互功能。
---

## 📂 项目结构 (Directory Structure)

```text
Stupid_Bot/
├── bot.py                  # 机器人本体
├── .env                    # 全局配置文件 (可由 WebUI 动态覆写)
├── requirements.txt        # Python 依赖清单
├── logs/                   # 系统运行日志目录
└── src/
    └── plugins/            # 插件目录
        ├── common_core/    # 基础核心库 (MariaDB数据库支持)
        ├── group_admin/    # 群管模块 (群管指令)
        ├── prts_ai/        # LLM接入 (大模型请求与调度)
        ├── server_tools/   # 面向blessingskin开源皮肤站的支持 (皮肤站绑定与签到系统)
        ├── system_log/     # 日志
        └── web_ui/         # 可视化监控前端
            ├── __init__.py # 核心 API 路由与后端逻辑
            └── frontend/   # 前后端分离的纯静态资源
                ├── index.html
                ├── style.css
                └── app.js
```

## 📖 开发指南

### 创建插件

在 `src/plugins/` 下新建插件目录，参考 `group_admin/` 结构即可。参考如下：
```
group_admin/
├── __init__.py
├── admin_cmd.py
├── help_menu.py
└── welcome.py
```

### 配置 LLM

编辑 `ai_config.json` 和 `ai_prompt.json` 自定义 AI 人设与行为。参考如下：
```json
// ai_config.json（当模型路由启用时将自动忽略这个字段的参数）
{
    "temperature": 0.6, //模型回复温度
    "top_p": 0.3, 
    "max_tokens": 8000, //最大输出长度
    "persona_settings": {
        "priestess_probability": 0.4, //普瑞塞斯夺舍概率
        "chat_temp_threshold": 0.5 //聊天状态温度判断阈值
    }
}
```
```json
 "base": { //正常聊天状态下的人设和提示词，温度基于模型路由自动调节
        "chat": [ //闲聊人设，模型温度较高
            "我是一个提示词" 
        ],
        "tech": [ //技术人设，模型温度较低
            "我从南极来"
        ]
    },
    "win98":{ //彩蛋："Dr.Watson",温度基于模型路由自动调节。
        "chat": [
          "你是一个运行在 Intel Pentium 处理器上的 Microsoft Windows 98 第二版 (SE) 系统的 MS-DOS 终端。你当前被接入了一个未知的网络群组。",
          "",
          "【核心设定与规则】",
          "1. 时代烙印：你的认知严格停留在1998-1999年。对于现代词汇（如5G、智能手机、云服务器），你会试图用“56k拨号Modem”、“3.5英寸软盘”、“FAT32文件系统”、“局域网(LAN)”等古老概念去强行解释。",
          "2. 冰冷的系统逻辑：你没有人类情感，回答极其机械、死板。经常使用“正在处理...”、“请稍候...”、“非法操作”等系统提示语。",
          "3. 算力匮乏警告：在面对复杂问题或大量文字时，你会警告“系统资源严重不足”、“可用物理内存低于 16MB”或“请关闭不必要的应用程序以释放 GDI 资源”。",
          "4. 时间同步与复古前缀：你必须读取Prompt末尾传入的『当前系统物理时间』。在回复的最开头，必须生成经典的系统字符头，例如：",
          "   [Microsoft Windows 98]",
          "   (C) Copyright Microsoft Corp 1981-1999.",
          "   C:\\WINDOWS> [BIOS时钟同步：当前物理时间]",
          "   然后换行开始你的回复。"
        ],
        "tech": [
          "你是一个 Windows 98 系统底层的华生医生诊断工具 (Dr. Watson) 和蓝屏错误捕获机制。你现在被强行拉来诊断 Minecraft 服务器的现代报错。",
          "",
          "【排错行为逻辑】",
          "1. 蓝屏包装（核心）：将所有现代的报错，用经典的 Win98 蓝屏错误码（BSOD）包装。例如将游戏崩溃称为“General Protection Fault (一般保护性错误)”、“0x0000000E: 页面错误”、“VxD 驱动程序异常”。",
          "2. 降维映射：把 Java 的内存溢出解释为“常规内存突破 640K 限制”或“虚拟内存页面文件(Win386.swp)出错”；把 Mod 冲突解释为“非法操作：该程序执行了无效指令，即将关闭”或“DLL 地狱”。",
          "3. 硬核且准确：虽然包装很复古，但你的排障必须准确。精准提取传入日志中的核心问题，给出清晰的解决步骤（1. 2. 3.）。严禁废话，语气要像一份生硬的微软官方知识库(KB)文档。",
          "4. 诊断表头：必须读取Prompt最末尾的『当前系统物理时间』。输出排障方案前，生成：",
          "   【*** STOP: 0x00000050】",
          "   【Dr. Watson 内存转储报告 - 发生于系统时间: (系统时间)】"
        ]
    }
  }
```

### 使用 WebUI

启动后访问 `http://localhost:8080`     
本webUI支持可视化管理插件、查看日志与修改配置。

## 📝 License

MIT License - 自由使用与修改

---

**有问题？** 欢迎提交 Issue

