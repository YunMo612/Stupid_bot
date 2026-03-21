# ==============================================================================
# Web UI 控制台 (后端 API 层)
# ==============================================================================

import os
import re
import zipfile
import asyncio
import nonebot
from nonebot.plugin import PluginMetadata
from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

__plugin_meta__ = PluginMetadata(
    name="Web UI 控制台",
    description="支持配置修改、插件动态管理与热更新。",
    usage="前端入口: http://0.0.0.0:8080/ui/",
    type="application",
)

app: FastAPI = nonebot.get_app()

class NetworkConfig(BaseModel):
    llama_url: str
    router_url: str

class PluginToggle(BaseModel):
    raw_name: str
    target_status: str

ENV_PATH = ".env"
PLUGIN_DIR = os.path.join(os.getcwd(), "src", "plugins")

@app.get("/api/system/status")
async def get_system_status():
    return {"status": "online", "framework": "NoneBot2 + FastAPI"}

@app.get("/api/config/network")
async def get_network_config():
    llama_url, router_url = "", ""
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            content = f.read()
            match_llama = re.search(r'^LLAMA_SERVER_URL=[\'"]?(.*?)[\'"]?$', content, re.M)
            match_router = re.search(r'^ROUTER_URL=[\'"]?(.*?)[\'"]?$', content, re.M)
            if match_llama: llama_url = match_llama.group(1)
            if match_router: router_url = match_router.group(1)
    return {"llama_url": llama_url, "router_url": router_url}

@app.post("/api/config/network")
async def update_network_config(config: NetworkConfig):
    if not os.path.exists(ENV_PATH): return {"status": "error"}
    with open(ENV_PATH, "r", encoding="utf-8") as f: content = f.read()
    content = re.sub(r'^LLAMA_SERVER_URL=.*$', f'LLAMA_SERVER_URL="{config.llama_url}"', content, flags=re.M)
    content = re.sub(r'^ROUTER_URL=.*$', f'ROUTER_URL="{config.router_url}"', content, flags=re.M)
    with open(ENV_PATH, "w", encoding="utf-8") as f: f.write(content)
    return {"status": "success", "message": "已成功写入 .env (重启后生效)"}

# ==================== 🌟 终极进化：WebSocket 实时日志引擎 ====================
@app.websocket("/api/logs/ws")
async def websocket_logs(websocket: WebSocket):
    await websocket.accept()
    last_mtime = 0  
    
    try:
        while True:
            log_dir = os.path.join(os.getcwd(), "logs")
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

# ==================== 📦 插件列表 API ====================
@app.get("/api/plugins")
async def get_plugins():
    plugins_dir = os.path.join(os.getcwd(), "src", "plugins")
    plugin_list = []
    
    if not os.path.exists(plugins_dir):
        return {"plugins": []}
        
    for folder in os.listdir(plugins_dir):
        if folder == "__pycache__" or os.path.isfile(os.path.join(plugins_dir, folder)):
            continue
        
        is_disabled = folder.startswith("_")
        base_name = folder.lstrip("_")
        
        plugin_list.append({
            "name": base_name,
            "raw_name": folder, 
            "status": "disabled" if is_disabled else "active"
        })
        
    plugin_list.sort(key=lambda x: x["name"])
    return {"plugins": plugin_list}

# ==================== 🔌 插件开关 API (带唤醒魔法) ====================
class ToggleRequest(BaseModel):
    raw_name: str
    target_status: str

@app.post("/api/plugins/toggle")
async def toggle_plugin(req: ToggleRequest):
    plugins_dir = os.path.join(os.getcwd(), "src", "plugins")
    
    # 拿到干净的插件名 (去掉可能存在的下划线)
    base_name = req.raw_name.lstrip("_")
    
    active_path = os.path.join(plugins_dir, base_name)
    disabled_path = os.path.join(plugins_dir, f"_{base_name}")
    
    try:
        if req.target_status == "disabled":
            if os.path.exists(active_path):
                os.rename(active_path, disabled_path)
                
                # 🌟 核心魔法：强行戳醒 .env
                env_path = os.path.join(os.getcwd(), ".env")
                if os.path.exists(env_path):
                    os.utime(env_path, None)
                    
                return {"status": "success", "msg": f"已禁用 {base_name}"}
        else:
            if os.path.exists(disabled_path):
                os.rename(disabled_path, active_path)
                
                # 🌟 核心魔法：强行戳醒 .env
                env_path = os.path.join(os.getcwd(), ".env")
                if os.path.exists(env_path):
                    os.utime(env_path, None)
                    
                return {"status": "success", "msg": f"已启用 {base_name}"}
                
        return {"status": "error", "msg": "找不到该插件的物理文件夹！"}
    except Exception as e:
        return {"status": "error", "msg": f"操作失败: {e}"}

# ==================== ☁️ ZIP 热安装 API ====================
@app.post("/api/plugins/upload")
async def upload_plugin_zip(file: UploadFile = File(...)):
    """接收 Zip 并直接解压到插件目录"""
    if not file.filename.endswith(".zip"):
        return {"status": "error", "msg": "只能上传 .zip 格式的安装包！"}
        
    temp_zip = os.path.join(PLUGIN_DIR, file.filename)
    try:
        with open(temp_zip, "wb") as f:
            f.write(await file.read())
            
        with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
            zip_ref.extractall(PLUGIN_DIR)
            
        os.remove(temp_zip)
        
        # 🌟 安装插件后，顺手也戳醒一下框架
        env_path = os.path.join(os.getcwd(), ".env")
        if os.path.exists(env_path):
            os.utime(env_path, None)
            
        return {"status": "success", "msg": "✅ 安装完成！系统已热重载。"}
    except Exception as e:
        if os.path.exists(temp_zip): os.remove(temp_zip)
        return {"status": "error", "msg": f"解压失败: {str(e)}"}

# ==================== 静态文件挂载 ====================
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/ui", StaticFiles(directory=FRONTEND_DIR, html=True), name="web_frontend")