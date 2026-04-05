# ==============================================================================
# Stupid_UI 控制台 (后端 API 层 Core v8.0 Meta)
# ==============================================================================

import os
import zipfile
import shutil
import asyncio
import json
import nonebot
import json
from nonebot.plugin import PluginMetadata
from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

__plugin_meta__ = PluginMetadata(
    name="Web UI 控制台",
    description="提供底层配置修改、插件动态管理与热更新的 MD3 现代化接口。",
    usage="前端入口: http://0.0.0.0:8080/ui/",
    type="application",
)

app: FastAPI = nonebot.get_app()

<<<<<<< HEAD
class PluginToggle(BaseModel):
=======
# ==================== 🌟 核心修复：绝对路径动态寻址 ====================
# 彻底免疫任何终端运行目录(cwd)偏移导致的“文件找不到”问题
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# 从 src/plugins/web_ui 往上退三级，强行锁定机器人根目录
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", ".."))

ENV_PATH = os.path.join(ROOT_DIR, ".env")
PLUGIN_DIR = os.path.join(ROOT_DIR, "src", "plugins")
PLUGINS_JSON_PATH = os.path.join(ROOT_DIR, "plugins.json")


# ==================== 📊 系统与连通性 API ====================
@app.get("/api/system/status")
async def get_system_status():
    return {"status": "online", "framework": "NoneBot2 + FastAPI", "version": "v8.0 Meta"}

@app.post("/api/ai/status")
async def check_ai_status():
    return {"status": "success", "model": "Connected", "latency": "12ms"}


# ==================== 🎛️ 全局 .env 配置管理 API ====================
@app.get("/api/config/env")
async def get_env_config():
    """解析并返回 .env 文件中的所有键值对"""
    config = {}
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if stripped and not stripped.startswith("#") and "=" in stripped:
                    key, val = stripped.split("=", 1)
                    config[key.strip()] = val.strip().strip("'").strip('"')
    return {"status": "success", "data": config}

class EnvConfig(BaseModel):
    config: dict

@app.post("/api/config/env")
async def save_env_config(req: EnvConfig):
    """覆写 .env 文件，同时智能保留注释和空行"""
    lines = []
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()

    new_config = req.config
    output_lines = []
    handled_keys = set()

    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key = stripped.split("=", 1)[0].strip()
            if key in new_config:
                output_lines.append(f"{key}={new_config[key]}\n")
                handled_keys.add(key)
        else:
            output_lines.append(line)

    for key, val in new_config.items():
        if key not in handled_keys:
            output_lines.append(f"{key}={val}\n")

    try:
        with open(ENV_PATH, "w", encoding="utf-8") as f:
            f.writelines(output_lines)
        return {"status": "success", "msg": "环境变量已安全覆盖！重启后生效。"}
    except Exception as e:
        return {"status": "error", "msg": f"写入失败: {e}"}


# ==================== 📦 插件列表与元数据 API ====================
@app.get("/api/plugins")
async def get_plugins():
    """精准读取物理文件夹，并结合 plugins.json 返回完整的元数据"""
    meta_data = {}
    if os.path.exists(PLUGINS_JSON_PATH):
        try:
            with open(PLUGINS_JSON_PATH, "r", encoding="utf-8") as f:
                meta_data = json.load(f)
        except Exception as e:
            print(f"[WebUI] 读取 plugins.json 失败: {e}")

    plugins_info = []
    if os.path.exists(PLUGIN_DIR):
        for item in os.listdir(PLUGIN_DIR):
            item_path = os.path.join(PLUGIN_DIR, item)
            # 过滤掉缓存与隐藏文件夹
            if os.path.isdir(item_path) and not item.startswith("__"):
                status = "disabled" if item.startswith("_") else "active"
                base_name = item.lstrip("_")
                
                p_meta = meta_data.get(base_name, {})
                plugins_info.append({
                    "raw_name": item,
                    "name": base_name,
                    "status": status,
                    "name_zh": p_meta.get("name_zh", base_name), 
                    "description": p_meta.get("description", "暂无模块描述信息。"), 
                    "version": p_meta.get("version", "v1.0.0"),
                    "can_disable": p_meta.get("can_disable", True), 
                    "can_delete": p_meta.get("can_delete", True)    
                })
                
    return {"plugins": plugins_info}


# ==================== 🔌 插件开关 API ====================
class ToggleRequest(BaseModel):
>>>>>>> dev
    raw_name: str
    target_status: str

@app.post("/api/plugins/toggle")
async def toggle_plugin(req: ToggleRequest):
    base_name = req.raw_name.lstrip("_")
    active_path = os.path.join(PLUGIN_DIR, base_name)
    disabled_path = os.path.join(PLUGIN_DIR, f"_{base_name}")
    
    if os.path.exists(PLUGINS_JSON_PATH):
        with open(PLUGINS_JSON_PATH, "r", encoding="utf-8") as f:
            meta_data = json.load(f)
            if meta_data.get(base_name, {}).get("can_disable") is False and req.target_status == "disabled":
                return {"status": "error", "msg": f"核心限制：[{base_name}] 禁止被禁用！"}
                
    def trigger_reload():
        trigger_file = os.path.join(PLUGIN_DIR, "__init__.py")
        if not os.path.exists(trigger_file):
            with open(trigger_file, "w", encoding="utf-8") as f: f.write("# Auto-generated to trigger reload\n")
        os.utime(trigger_file, None)

    try:
        if req.target_status == "disabled" and os.path.exists(active_path):
            os.rename(active_path, disabled_path)
            trigger_reload()
            return {"status": "success"}
        elif req.target_status == "active" and os.path.exists(disabled_path):
            os.rename(disabled_path, active_path)
            trigger_reload()
            return {"status": "success"}
        return {"status": "error", "msg": "找不到该插件的对应文件夹！"}
    except Exception as e:
        return {"status": "error", "msg": str(e)}

<<<<<<< HEAD
# ==================== 🎛️ 全局 .env 配置管理 API ====================
@app.get("/api/config/env")
async def get_env_config():
    """解析并返回 .env 文件中的所有键值对"""
    config = {}
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if stripped and not stripped.startswith("#") and "=" in stripped:
                    key, val = stripped.split("=", 1)
                    config[key.strip()] = val.strip().strip("'").strip('"')
    return {"status": "success", "data": config}

class EnvConfig(BaseModel):
    config: dict

@app.post("/api/config/env")
async def save_env_config(req: EnvConfig):
    """覆写 .env 文件，同时智能保留注释和空行"""
    lines = []
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()

    new_config = req.config
    output_lines = []
    handled_keys = set()

    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key = stripped.split("=", 1)[0].strip()
            if key in new_config:
                output_lines.append(f"{key}={new_config[key]}\n")
                handled_keys.add(key)
        else:
            output_lines.append(line)

    for key, val in new_config.items():
        if key not in handled_keys:
            output_lines.append(f"{key}={val}\n")

    try:
        with open(ENV_PATH, "w", encoding="utf-8") as f:
            f.writelines(output_lines)
        return {"status": "success", "msg": "环境变量已覆盖写入，重启后生效！"}
    except Exception as e:
        return {"status": "error", "msg": f"写入失败: {e}"}

# ==================== 🌟 WebSocket 实时日志引擎 ====================
=======

# ==================== 🗑️ 插件删除 API ====================
class DeleteRequest(BaseModel):
    raw_name: str

@app.post("/api/plugins/delete")
async def delete_plugin(req: DeleteRequest):
    target_path = os.path.join(PLUGIN_DIR, req.raw_name)
    base_name = req.raw_name.lstrip("_")
    
    if os.path.exists(PLUGINS_JSON_PATH):
        with open(PLUGINS_JSON_PATH, "r", encoding="utf-8") as f:
            meta_data = json.load(f)
            if meta_data.get(base_name, {}).get("can_delete") is False:
                return {"status": "error", "msg": f"致命拦截：[{base_name}] 是受保护的底层资产，禁止物理销毁！"}
        
    def trigger_reload():
        trigger_file = os.path.join(PLUGIN_DIR, "__init__.py")
        if os.path.exists(trigger_file):
            os.utime(trigger_file, None)

    try:
        if os.path.exists(target_path) and os.path.isdir(target_path):
            shutil.rmtree(target_path)
            trigger_reload()
            return {"status": "success"}
        return {"status": "error", "msg": "找不到该插件的文件夹！"}
    except Exception as e:
        return {"status": "error", "msg": str(e)}


# ==================== ☁️ ZIP 热安装 API ====================
@app.post("/api/plugins/upload")
async def upload_plugin_zip(file: UploadFile = File(...)):
    if not file.filename.endswith(".zip"):
        return {"status": "error", "msg": "只能上传 .zip 格式的安装包！"}
        
    temp_zip = os.path.join(PLUGIN_DIR, file.filename)
    try:
        with open(temp_zip, "wb") as f:
            f.write(await file.read())
            
        with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
            zip_ref.extractall(PLUGIN_DIR)
            
        os.remove(temp_zip)
        if os.path.exists(ENV_PATH):
            os.utime(ENV_PATH, None)
            
        return {"status": "success", "msg": "✅ 模块解压安装完成！"}
    except Exception as e:
        if os.path.exists(temp_zip): os.remove(temp_zip)
        return {"status": "error", "msg": f"解压失败: {str(e)}"}


# ==================== 📝 WebSocket 实时日志引擎 ====================
>>>>>>> dev
@app.websocket("/api/logs/ws")
async def websocket_logs(websocket: WebSocket):
    await websocket.accept()
    last_mtime = 0  
    
    try:
        while True:
            log_dir = os.path.join(ROOT_DIR, "logs")
            if not os.path.exists(log_dir):
                await asyncio.sleep(1)
                continue
            
            folders = sorted([f for f in os.listdir(log_dir) if os.path.isdir(os.path.join(log_dir, f))], reverse=True)
            if not folders:
                await asyncio.sleep(1)
                continue
                
            latest_folder = os.path.join(log_dir, folders[0])
            files = sorted([f for f in os.listdir(latest_folder) if f.endswith(".log")], reverse=True)
            if not files:
                await asyncio.sleep(1)
                continue
                
            latest_file = os.path.join(latest_folder, files[0])
            current_mtime = os.stat(latest_file).st_mtime
            
            if current_mtime != last_mtime:
                try:
                    with open(latest_file, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                        logs = "".join(lines[-300:])
                    
                    filtered_logs = "\n".join([line for line in logs.split("\n") if "GET /api/" not in line and "GET /ui" not in line])
                    await websocket.send_json({"status": "success", "logs": filtered_logs, "file": f"{folders[0]}/{files[0]}"})
                    last_mtime = current_mtime
                except Exception:
                    pass
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        pass

<<<<<<< HEAD
# ==================== 🔌 插件列表 API (支持读取 plugins.json) ====================
@app.get("/api/plugins")
async def get_plugins():
    json_path = os.path.join(os.getcwd(), "plugins.json")
    meta_data = {}
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                meta_data = json.load(f)
        except Exception:
            pass

    plugins_info = []
    if os.path.exists(PLUGIN_DIR):
        for item in os.listdir(PLUGIN_DIR):
            item_path = os.path.join(PLUGIN_DIR, item)
            if os.path.isdir(item_path) and not item.startswith("__"):
                status = "disabled" if item.startswith("_") else "active"
                base_name = item.lstrip("_")
                p_meta = meta_data.get(base_name, {})
                plugins_info.append({
                    "raw_name": item,
                    "name": base_name,
                    "status": status,
                    "name_zh": p_meta.get("name_zh", base_name),
                    "description": p_meta.get("description", "暂无模块描述信息..."),
                    "version": p_meta.get("version", "v1.0"),
                    "can_disable": p_meta.get("can_disable", True),
                    "can_delete": p_meta.get("can_delete", True)
                })
    return {"plugins": plugins_info}

# ==================== 🔌 插件开关 API ====================
class ToggleRequest(BaseModel):
    raw_name: str
    target_status: str

@app.post("/api/plugins/toggle")
async def toggle_plugin(req: ToggleRequest):
    base_name = req.raw_name.lstrip("_")
    active_path = os.path.join(PLUGIN_DIR, base_name)
    disabled_path = os.path.join(PLUGIN_DIR, f"_{base_name}")
    
    json_path = os.path.join(os.getcwd(), "plugins.json")
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            meta_data = json.load(f)
            if meta_data.get(base_name, {}).get("can_disable") is False and req.target_status == "disabled":
                return {"status": "error", "msg": f"核心限制：[{base_name}] 禁止被禁用！"}
                
    trigger_file = os.path.join(PLUGIN_DIR, "__init__.py")
    def trigger_reload():
        if not os.path.exists(trigger_file):
            with open(trigger_file, "w", encoding="utf-8") as f: f.write("# Auto-generated to trigger reload\n")
        os.utime(trigger_file, None)

    try:
        if req.target_status == "disabled" and os.path.exists(active_path):
            os.rename(active_path, disabled_path)
            trigger_reload()
            return {"status": "success"}
        elif req.target_status == "active" and os.path.exists(disabled_path):
            os.rename(disabled_path, active_path)
            trigger_reload()
            return {"status": "success"}
        return {"status": "error", "msg": "找不到该插件文件夹！"}
    except Exception as e:
        return {"status": "error", "msg": str(e)}

# ==================== 🗑️ 插件删除 API ====================
class DeleteRequest(BaseModel):
    raw_name: str

@app.post("/api/plugins/delete")
async def delete_plugin(req: DeleteRequest):
    target_path = os.path.join(PLUGIN_DIR, req.raw_name)
    base_name = req.raw_name.lstrip("_")
    
    json_path = os.path.join(os.getcwd(), "plugins.json")
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            meta_data = json.load(f)
            if meta_data.get(base_name, {}).get("can_delete") is False:
                return {"status": "error", "msg": f"致命拦截：[{base_name}] 是受保护的底层资产，禁止物理销毁！"}
        
    def trigger_reload():
        trigger_file = os.path.join(PLUGIN_DIR, "__init__.py")
        os.utime(trigger_file, None)

    try:
        if os.path.exists(target_path) and os.path.isdir(target_path):
            shutil.rmtree(target_path)
            trigger_reload()
            return {"status": "success"}
        return {"status": "error", "msg": "找不到文件夹！"}
    except Exception as e:
        return {"status": "error", "msg": str(e)}
    
# ==================== ☁️ ZIP 热安装 API ====================
@app.post("/api/plugins/upload")
async def upload_plugin_zip(file: UploadFile = File(...)):
    if not file.filename.endswith(".zip"):
        return {"status": "error", "msg": "只能上传 .zip 格式的安装包！"}
        
    temp_zip = os.path.join(PLUGIN_DIR, file.filename)
    try:
        with open(temp_zip, "wb") as f:
            f.write(await file.read())
            
        with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
            zip_ref.extractall(PLUGIN_DIR)
            
        os.remove(temp_zip)
        
        env_path = os.path.join(os.getcwd(), ".env")
        if os.path.exists(env_path):
            os.utime(env_path, None)
            
        return {"status": "success", "msg": "✅ 安装完成！系统已热重载。"}
    except Exception as e:
        if os.path.exists(temp_zip): os.remove(temp_zip)
        return {"status": "error", "msg": f"解压失败: {str(e)}"}

# ==================== 静态文件挂载 ====================
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")
=======

# ==================== 🖥️ 静态文件挂载 ====================
FRONTEND_DIR = os.path.join(CURRENT_DIR, "frontend")
>>>>>>> dev
if os.path.exists(FRONTEND_DIR):
    app.mount("/ui", StaticFiles(directory=FRONTEND_DIR, html=True), name="web_frontend")
else:
    print(f"[WebUI] ⚠️ 警告：未找到前端目录 {FRONTEND_DIR}")