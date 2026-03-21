# ==============================================================================
# Web UI 控制台 (后端 API 层)
# ==============================================================================

import os
import re
import zipfile
import nonebot
from nonebot.plugin import PluginMetadata
from fastapi import FastAPI, UploadFile, File
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

__plugin_meta__ = PluginMetadata(
    name="Web UI 控制台",
    description="支持配置修改、插件动态管理与热更新。",
    usage="前端入口: http://你的IP:8080/ui/",
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

# (省略的 /api/system/status 和 /api/config/network 接口保持不变...)
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

# ==================== 🌟 新增：实时日志 API ====================
@app.get("/api/logs/latest")
async def get_latest_logs():
    """读取今天最新的日志文件（为了性能，截取最后 300 行）"""
    log_dir = os.path.join(os.getcwd(), "logs")
    if not os.path.exists(log_dir):
        return {"status": "error", "logs": "日志总目录不存在，等待框架生成...", "file": ""}
    
    # 1. 找最新的日期文件夹 (按名字倒序，第一个就是最新的)
    folders = sorted([f for f in os.listdir(log_dir) if os.path.isdir(os.path.join(log_dir, f))], reverse=True)
    if not folders:
        return {"status": "error", "logs": "暂无日期文件夹。", "file": ""}
        
    latest_folder = os.path.join(log_dir, folders[0])
    
    # 2. 找文件夹里最新的 .log 文件
    files = sorted([f for f in os.listdir(latest_folder) if f.endswith(".log")], reverse=True)
    if not files:
        return {"status": "error", "logs": f"[{folders[0]}] 文件夹下暂无日志文件。", "file": ""}
        
    latest_file = os.path.join(latest_folder, files[0])
    
    # 3. 读取最后 300 行数据
    try:
        with open(latest_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            # 取最后300行，防止前端一次性渲染数万行卡死
            logs = "".join(lines[-300:]) 
            return {"status": "success", "logs": logs, "file": f"{folders[0]}/{files[0]}"}
    except Exception as e:
        return {"status": "error", "logs": f"读取日志文件失败: {e}", "file": ""}

# ==================== 🌟 核心：插件管理 API ====================
@app.get("/api/plugins")
async def get_plugin_list():
    """扫描目录下的插件状态"""
    plugins = []
    if os.path.exists(PLUGIN_DIR):
        for item in os.listdir(PLUGIN_DIR):
            if item == "__pycache__" or item.startswith("."): continue
            
            # 识别被我们特殊标记的禁用文件夹
            is_disabled = item.startswith("_disabled_")
            display_name = item.replace("_disabled_", "") if is_disabled else item
            
            plugins.append({
                "name": display_name,
                "raw_name": item,
                "status": "disabled" if is_disabled else "active"
            })
    return {"plugins": sorted(plugins, key=lambda x: x["name"])}

@app.post("/api/plugins/toggle")
async def toggle_plugin(req: PluginToggle):
    """通过重命名文件夹实现动态禁用/启用，触发底层热重载"""
    old_path = os.path.join(PLUGIN_DIR, req.raw_name)
    if not os.path.exists(old_path): return {"status": "error", "msg": "找不到插件目录"}
    
    new_name = f"_disabled_{req.raw_name}" if req.target_status == "disabled" else req.raw_name.replace("_disabled_", "")
    new_path = os.path.join(PLUGIN_DIR, new_name)
    
    os.rename(old_path, new_path)
    # 返回成功，此时底层 Uvicorn 会察觉到文件变化，在后台自动重启！
    return {"status": "success", "msg": f"插件已{'禁用' if req.target_status == 'disabled' else '启用'}！系统正在热重载..."}

@app.post("/api/plugins/upload")
async def upload_plugin_zip(file: UploadFile = File(...)):
    """接收 Zip 并直接解压到插件目录"""
    if not file.filename.endswith(".zip"):
        return {"status": "error", "msg": "只能上传 .zip 格式的安装包！"}
        
    temp_zip = os.path.join(PLUGIN_DIR, file.filename)
    try:
        # 1. 保存 zip
        with open(temp_zip, "wb") as f:
            f.write(await file.read())
        # 2. 解压到插件目录
        with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
            zip_ref.extractall(PLUGIN_DIR)
        # 3. 销毁安装包
        os.remove(temp_zip)
        return {"status": "success", "msg": "✅ 安装完成！系统已热重载。"}
    except Exception as e:
        if os.path.exists(temp_zip): os.remove(temp_zip)
        return {"status": "error", "msg": f"解压失败: {str(e)}"}

# ==================== 静态文件挂载 ====================
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/ui", StaticFiles(directory=FRONTEND_DIR, html=True), name="web_frontend")