// ==========================================
// PRTS 终端控制台 - 核心逻辑脚本 (完全体 v4)
// ==========================================

// === 1. 核心状态与主题切换 ===
let isDarkTheme = true;
let isTransitioning = false;

function performThemeSwitch() {
    const body = document.body;
    const themeBtn = document.getElementById('theme-btn');
    isDarkTheme = !isDarkTheme;
    
    if (isDarkTheme) {
        body.classList.add('dark-theme');
        themeBtn.innerHTML = '☀️'; // 提示切到白天
    } else {
        body.classList.remove('dark-theme');
        themeBtn.innerHTML = '🌙'; // 提示切到黑夜
    }
}

async function toggleTheme(event) {
    if (isTransitioning) return;
    if (!document.startViewTransition) { performThemeSwitch(); return; }
    
    isTransitioning = true;
    
    // 获取悬浮按钮的中心点，作为动画圆心
    const btn = event.currentTarget;
    const rect = btn.getBoundingClientRect();
    const x = rect.left + rect.width / 2;
    const y = rect.top + rect.height / 2;
    
    // 计算屏幕最远角，确保遮罩能覆盖全屏
    const endRadius = Math.hypot(
        Math.max(x, window.innerWidth - x), 
        Math.max(y, window.innerHeight - y)
    );
    
    document.documentElement.classList.add('theme-transitioning');
    
    const transition = document.startViewTransition(() => { 
        performThemeSwitch(); 
    });
    
    await transition.ready;
    
    const start = performance.now();
    const duration = 650; // 动画时长稍微拉长，让羽化过程更细腻
    
    function animateMask(time) {
        let progress = (time - start) / duration;
        if (progress > 1) progress = 1;
        
        // 缓动算法：前段加速，后段平滑减速
        const easeOut = 1 - Math.pow(1 - progress, 4);
        let currentRadius = endRadius * easeOut;
        
        // 防止初始半径过小导致 CSS calc(radius - 15px) 出现负数渲染错误
        if (currentRadius < 15) currentRadius = 15;
        
        // 逐帧更新 CSS 变量，传递给 mask-image
        document.documentElement.style.setProperty('--mask-x', x + 'px');
        document.documentElement.style.setProperty('--mask-y', y + 'px');
        document.documentElement.style.setProperty('--mask-radius', currentRadius + 'px');
        
        if (progress < 1) {
            requestAnimationFrame(animateMask);
        } else { 
            document.documentElement.classList.remove('theme-transitioning'); 
            isTransitioning = false; 
        }
    }
    
    requestAnimationFrame(animateMask);
}

// === 2. 菜单栏切换逻辑 ===
let ws = null;

function switchTab(pageId, element, title) {
    document.querySelectorAll('.menu-item').forEach(item => item.classList.remove('active'));
    element.classList.add('active');
    
    const topbarTitle = document.getElementById('topbar-title');
    if(topbarTitle) topbarTitle.innerText = title;
    
    document.querySelectorAll('.page-container').forEach(page => page.classList.remove('active'));
    document.getElementById(pageId).classList.add('active');
    
    if (ws) { ws.close(); ws = null; }
    
    if (pageId === 'page-network') loadNetworkConfig();
    if (pageId === 'page-plugins') loadPlugins();
    if (pageId === 'page-logs') initLogWebSocket(); 
}

// === 3. 系统与大模型监控 API ===
async function checkSystem() {
    const box = document.getElementById('status-box');
    box.innerText = '正在请求系统 API...';
    try {
        const res = await fetch('/api/system/status');
        const data = await res.json();
        box.innerHTML = `<span style="color:#81a1c1;">[SYSTEM INFO]</span>\n${JSON.stringify(data, null, 2)}`;
    } catch (e) { box.innerHTML = `<span style="color:#bf616a;">[ERROR]</span> 系统接口掉线：${e.message}`; }
}

async function checkAI() {
    const box = document.getElementById('status-box');
    box.innerText = '正在 PING 大模型核心节点...';
    try {
        const res = await fetch('/api/ai/status', {method: 'POST'});
        const data = await res.json();
        box.innerHTML = `<span style="color:#b48ead;">[AI CORE OK]</span>\n${JSON.stringify(data, null, 2)}`;
    } catch (e) { box.innerHTML = `<span style="color:#bf616a;">[ERROR]</span> 大模型节点未响应。请检查 prts_ai 模块是否加载。`; }
}

// === 4. 网络配置读取与保存 ===
async function loadNetworkConfig() {
    try {
        const res = await fetch('/api/config/network');
        const data = await res.json();
        document.getElementById('input-llama').value = data.llama_url || "";
        document.getElementById('input-router').value = data.router_url || "";
    } catch(e) { console.error("读取配置失败", e); }
}

async function saveNetworkConfig() {
    const btn = document.getElementById('btn-save-net');
    const msg = document.getElementById('save-msg');
    const llama_url = document.getElementById('input-llama').value.trim();
    const router_url = document.getElementById('input-router').value.trim();
    btn.innerText = "⏳ 保存中...";
    try {
        const res = await fetch('/api/config/network', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({llama_url, router_url}) });
        const data = await res.json();
        if (data.status === 'success') { msg.style.color = "#a3be8c"; msg.innerText = "✔️ " + data.message; } 
        else { msg.style.color = "#bf616a"; msg.innerText = "❌ " + data.message; }
    } catch(e) { msg.style.color = "#bf616a"; msg.innerText = "❌ 网络请求失败"; }
    btn.innerText = "💾 保存配置到 .env";
    setTimeout(() => { msg.innerText = ""; }, 3000);
}

// === 5. 插件动态管理 ===
async function loadPlugins() {
    const list = document.getElementById('plugin-list');
    try {
        const res = await fetch('/api/plugins');
        const data = await res.json();
        list.innerHTML = "";
        data.plugins.forEach(p => {
            const isActive = p.status === 'active';
            const dotClass = isActive ? 'status-active' : 'status-disabled';
            const btnClass = isActive ? 'btn-disable' : 'btn-enable';
            const btnText = isActive ? '禁用模块' : '启用模块';
            const statusText = isActive ? 'ACTIVE' : 'DISABLED';
            const color = isActive ? '#a3be8c' : '#bf616a';
            
            const isCore = p.name === 'web_ui' || p.name === 'common_core';
            const deleteBtnHtml = isCore ? 
                `<span class="core-protect-text">[核心锁定]</span>` : 
                `<button class="delete-btn" onclick="openDeleteModal('${p.raw_name}')">🗑️ 销毁</button>`;

            list.innerHTML += `
                <div class="plugin-item">
                    <div class="plugin-info">
                        <div class="status-dot ${dotClass}"></div>
                        <span style="color:var(--text-main); font-family: 'Consolas', monospace; font-size: 1.1rem;">${p.name}</span>
                        <span style="font-size: 0.8rem; color:${color}; border: 1px solid ${color}; padding: 2px 6px; border-radius: 4px; margin-left: 10px;">${statusText}</span>
                    </div>
                    <div style="display: flex; align-items: center;">
                        <button class="toggle-btn ${btnClass}" onclick="togglePlugin('${p.raw_name}', '${isActive ? 'disabled' : 'active'}')">${btnText}</button>
                        ${deleteBtnHtml}
                    </div>
                </div>
            `;
        });
    } catch(e) { list.innerHTML = "<div style='color:#bf616a;'>读取列表失败</div>"; }
}

async function togglePlugin(rawName, targetStatus) {
    try {
        await fetch('/api/plugins/toggle', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({raw_name: rawName, target_status: targetStatus}) });
        document.getElementById('plugin-list').innerHTML = "<div style='color:#ebcb8b; text-align:center; padding: 20px;'>🔄 底层引擎热重载中，请稍候...</div>";
        setTimeout(() => { loadPlugins(); }, 2000);
    } catch(e) { console.error("切换失败"); }
}

// === 弹窗状态管理机制 ===
let currentPluginToDelete = null;

// 1. 打开自定义确认弹窗
function openDeleteModal(rawName) {
    currentPluginToDelete = rawName;
    const cleanName = rawName.replace(/^_/, ""); 
    document.getElementById('delete-plugin-name').innerText = cleanName;
    document.getElementById('delete-modal').classList.add('show');
}

// 2. 关闭弹窗
function closeDeleteModal() {
    currentPluginToDelete = null;
    document.getElementById('delete-modal').classList.remove('show');
}

// 3. 💥 确认执行物理销毁 (从弹窗内部触发)
async function executeDelete() {
    if (!currentPluginToDelete) return;
    const rawName = currentPluginToDelete;
    
    // 先关掉弹窗
    closeDeleteModal();
    
    // 界面进入加载状态
    document.getElementById('plugin-list').innerHTML = "<div style='color:#bf616a; text-align:center; padding: 20px;'>🗑️ 正在执行物理清除，底层引擎即将重启...</div>";
    
    try {
        const res = await fetch('/api/plugins/delete', { 
            method: 'POST', 
            headers: {'Content-Type': 'application/json'}, 
            body: JSON.stringify({raw_name: rawName}) 
        });
        const data = await res.json();
        
        if (data.status === 'success') { 
            setTimeout(() => { loadPlugins(); }, 2000); 
        } else { 
            alert(data.msg); 
            loadPlugins(); 
        }
    } catch(e) { 
        alert("网络请求失败，销毁指令未送达。"); 
        loadPlugins(); 
    }
}

// === 6. Zip 插件拖拽上传 ===
document.addEventListener("DOMContentLoaded", () => {
    const dropZone = document.getElementById("drop-zone");
    const dropMsg = document.getElementById("drop-msg");
    const fileInput = document.getElementById("file-input");
    if (!dropZone) return;
    
    dropZone.addEventListener("click", () => fileInput.click());
    dropZone.addEventListener("dragover", (e) => { e.preventDefault(); dropZone.classList.add("dragover"); dropMsg.innerText = "放开鼠标立即安装！"; });
    dropZone.addEventListener("dragleave", () => { dropZone.classList.remove("dragover"); dropMsg.innerText = "将包含 __init__.py 的插件 .zip 包拖拽到此处进行热安装"; });
    dropZone.addEventListener("drop", (e) => { e.preventDefault(); dropZone.classList.remove("dragover"); if (e.dataTransfer.files.length > 0) handleFileUpload(e.dataTransfer.files[0]); });
    fileInput.addEventListener("change", (e) => { if (e.target.files.length > 0) handleFileUpload(e.target.files[0]); });

    async function handleFileUpload(file) {
        if (!file.name.endsWith(".zip")) { alert("请上传 .zip 压缩包！"); return; }
        dropMsg.style.color = "#ebcb8b"; dropMsg.innerText = "⏳ 正在传输并解压到内核...";
        const formData = new FormData(); formData.append("file", file);
        try {
            const res = await fetch('/api/plugins/upload', { method: 'POST', body: formData });
            const data = await res.json();
            if (data.status === 'success') {
                dropMsg.style.color = "#a3be8c"; dropMsg.innerText = data.msg;
                setTimeout(() => { dropMsg.innerText = "将包含 __init__.py 的插件 .zip 包拖拽到此处进行热安装"; dropMsg.style.color = ""; loadPlugins(); }, 2000);
            } else { dropMsg.style.color = "#bf616a"; dropMsg.innerText = data.msg; }
        } catch(e) { dropMsg.style.color = "#bf616a"; dropMsg.innerText = "❌ 上传网络中断！"; }
    }
});

// === 7. 实时日志渲染系统 ===
let autoScroll = true;

function toggleAutoScroll() {
    autoScroll = !autoScroll;
    const btn = document.getElementById('auto-scroll-btn');
    if (autoScroll) { btn.innerText = "自动滚动: 开启"; btn.className = "toggle-btn btn-disable"; } 
    else { btn.innerText = "自动滚动: 暂停"; btn.className = "toggle-btn btn-enable"; }
}

window.loadLogs = function() {
    if (ws) ws.close();
    initLogWebSocket();
};

function initLogWebSocket() {
    const consoleBox = document.getElementById('log-console');
    if(!consoleBox) return;
    consoleBox.innerHTML = '<span style="color:#ebcb8b;">[SYSTEM] 正在建立 WebSocket 神经管道...</span>';
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/logs/ws`;
    
    ws = new WebSocket(wsUrl);
    const refreshBtn = document.querySelector('button[onclick="loadLogs()"]');
    if(refreshBtn) refreshBtn.innerText = "重连管道";
    
    ws.onmessage = function(event) {
        const data = JSON.parse(event.data);
        if (data.status === 'success') {
            const nameLabel = document.getElementById('log-file-name');
            if(nameLabel) nameLabel.innerText = "读取文件: " + data.file;
            
            let html = data.logs.replace(/</g, "&lt;").replace(/>/g, "&gt;");
            html = html.replace(/SUCCESS/g, '<span style="color: #a3be8c; font-weight: bold;">SUCCESS</span>');
            html = html.replace(/INFO/g, '<span style="color: #81a1c1; font-weight: bold;">INFO</span>');
            html = html.replace(/WARNING/g, '<span style="color: #ebcb8b; font-weight: bold;">WARNING</span>');
            html = html.replace(/ERROR/g, '<span style="color: #bf616a; font-weight: bold;">ERROR</span>');
            html = html.replace(/Traceback \(most recent call last\):/g, '<span style="color: #bf616a; text-decoration: underline;">Traceback (most recent call last):</span>');
            
            consoleBox.innerHTML = html;
            if (autoScroll) consoleBox.scrollTop = consoleBox.scrollHeight;
        }
    };
    ws.onclose = function() {
        const pageLogs = document.getElementById('page-logs');
        if (pageLogs && pageLogs.classList.contains('active')) {
            consoleBox.innerHTML += '\n<span style="color:#bf616a;">[SYSTEM] 管道已断开，正在尝试重连...</span>';
            setTimeout(initLogWebSocket, 3000);
        }
    };
}