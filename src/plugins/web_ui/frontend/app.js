// ==========================================
// PRTS 终端控制台 - 核心逻辑脚本 (完全体 v9)
// ==========================================

// === 0. 🎨 莫奈取色引擎与全局光影 ===
function initMonetEngine(customSrc = null) {
    const savedBg = localStorage.getItem('prts_custom_bg');
    const bgUrl = customSrc || savedBg || './background/bg.png';
    
    document.body.style.backgroundImage = `url('${bgUrl}')`;

    const img = new Image();
    img.crossOrigin = "Anonymous";
    img.src = bgUrl;
    
    img.onload = () => {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        canvas.width = img.width; canvas.height = img.height;
        ctx.drawImage(img, 0, 0, img.width, img.height);
        try {
            const data = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
            let r=0, g=0, b=0, count=0;
            for (let i = 0; i < data.length; i += 400) {
                if (data[i] > 30 && data[i] < 230 && data[i+3] > 128) { r += data[i]; g += data[i+1]; b += data[i+2]; count++; }
            }
            if(count > 0) {
                r = Math.floor(r / count); g = Math.floor(g / count); b = Math.floor(b / count);
                const boost = 1.3;
                r = Math.min(255, Math.floor(r * boost)); g = Math.min(255, Math.floor(g * boost)); b = Math.min(255, Math.floor(b * boost));
                document.documentElement.style.setProperty('--monet-rgb', `${r}, ${g}, ${b}`);
            }
        } catch(e) {}
    };
    img.onerror = () => {
        document.body.style.backgroundImage = "linear-gradient(135deg, #0f1016, #212436)";
        document.documentElement.style.setProperty('--monet-rgb', '100, 150, 255');
    };
}

window.resetBackground = function() {
    localStorage.removeItem('prts_custom_bg');
    initMonetEngine('./background/bg.jpg');
    const msg = document.getElementById('bg-upload-msg');
    if(msg) { msg.style.color = "var(--log-info)"; msg.innerText = "✔️ 已恢复默认深空"; setTimeout(()=>msg.innerText="", 3000); }
}

function initInteractiveLighting() {
    const panels = document.querySelectorAll('[data-interactive="true"]');
    if (panels.length === 0) return;
    document.addEventListener("mousemove", (event) => {
        panels.forEach((panel) => {
            const rect = panel.getBoundingClientRect();
            panel.style.setProperty('--light-x', `${event.clientX - rect.left}px`);
            panel.style.setProperty('--light-y', `${event.clientY - rect.top}px`);
        });
    });
}

function initBackgroundUpload() {
    const bgUpload = document.getElementById('bg-upload');
    const msg = document.getElementById('bg-upload-msg');
    if (!bgUpload) return;
    
    bgUpload.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (!file) return;
        msg.style.color = "var(--log-warn)"; msg.innerText = "⏳ 正在压缩...";
        
        const reader = new FileReader();
        reader.onload = (evt) => {
            const img = new Image();
            img.onload = () => {
                const canvas = document.createElement('canvas');
                let w = img.width; let h = img.height;
                const MAX_SIZE = 1920; 
                if (w > MAX_SIZE || h > MAX_SIZE) {
                    if (w > h) { h = Math.round((h *= MAX_SIZE / w)); w = MAX_SIZE; } 
                    else { w = Math.round((w *= MAX_SIZE / h)); h = MAX_SIZE; }
                }
                canvas.width = w; canvas.height = h;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(img, 0, 0, w, h);
                const compressedDataUrl = canvas.toDataURL('image/jpeg', 0.8);
                
                try {
                    localStorage.setItem('prts_custom_bg', compressedDataUrl);
                    initMonetEngine(compressedDataUrl);
                    msg.style.color = "var(--log-success)"; msg.innerText = "✔️ 壁纸已保存！";
                } catch(err) {
                    msg.style.color = "var(--log-error)"; msg.innerText = "❌ 图片过大";
                }
                setTimeout(()=>msg.innerText="", 4000);
            };
            img.src = evt.target.result;
        };
        reader.readAsDataURL(file);
    });
}

document.addEventListener("DOMContentLoaded", () => {
    initMonetEngine();
    initInteractiveLighting();
    initBackgroundUpload();
});

// === 1. 🌟 主题扩散切换动画 (以按钮为完美圆心) ===
let isDarkTheme = true;
let isTransitioning = false;

function performThemeSwitch() {
    const body = document.body;
    const themeBtn = document.getElementById('theme-btn');
    isDarkTheme = !isDarkTheme;
    if (isDarkTheme) { body.classList.add('dark-theme'); themeBtn.innerHTML = '☀️'; } 
    else { body.classList.remove('dark-theme'); themeBtn.innerHTML = '🌙'; }
}

async function toggleTheme(event) {
    if (isTransitioning) return;
    if (!document.startViewTransition) { performThemeSwitch(); return; }
    
    isTransitioning = true;
    
    // 💡 核心：精确捕捉按钮在当前视口中的绝对中心点
    const btn = event.currentTarget;
    const rect = btn.getBoundingClientRect();
    const x = rect.left + rect.width / 2;
    const y = rect.top + rect.height / 2;
    
    // 计算以按钮为圆心，能覆盖全屏所需的最大半径
    const endRadius = Math.hypot(Math.max(x, window.innerWidth - x), Math.max(y, window.innerHeight - y));
    document.documentElement.classList.add('theme-transitioning');
    
    const transition = document.startViewTransition(() => { performThemeSwitch(); });
    await transition.ready;
    const start = performance.now();
    
    function animateMask(time) {
        let progress = (time - start) / 700; // 稍微放慢，让 30px 羽化更显柔和
        if (progress > 1) progress = 1;
        
        // 使用 ease-out 缓动，产生类似波纹爆开的自然感
        const easeOut = 1 - Math.pow(1 - progress, 4);
        let currentRadius = endRadius * easeOut;
        
        // 保证起始半径足够容纳 30px 羽化，防止渲染黑块
        if (currentRadius < 30) currentRadius = 30; 
        
        document.documentElement.style.setProperty('--mask-x', x + 'px');
        document.documentElement.style.setProperty('--mask-y', y + 'px');
        document.documentElement.style.setProperty('--mask-radius', currentRadius + 'px');
        
        if (progress < 1) requestAnimationFrame(animateMask);
        else { document.documentElement.classList.remove('theme-transitioning'); isTransitioning = false; }
    }
    requestAnimationFrame(animateMask);
}

// === 2. 📱 移动端抽屉菜单逻辑 ===
function toggleMobileMenu() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('mobile-overlay');
    
    if (sidebar.classList.contains('mobile-open')) {
        sidebar.classList.remove('mobile-open');
        overlay.classList.remove('show');
    } else {
        sidebar.classList.add('mobile-open');
        overlay.classList.add('show');
    }
}

// === 3. 菜单导航 ===
let ws = null;
function switchTab(pageId, element, title) {
    document.querySelectorAll('.menu-item').forEach(item => item.classList.remove('active'));
    element.classList.add('active');
    const topbarTitle = document.getElementById('topbar-title');
    if(topbarTitle) topbarTitle.innerText = title;
    document.querySelectorAll('.page-container').forEach(page => page.classList.remove('active'));
    document.getElementById(pageId).classList.add('active');
    
    // 如果在手机端，点击菜单后自动收起侧边栏
    if (window.innerWidth <= 768) {
        toggleMobileMenu();
    }
    
    if (ws) { ws.close(); ws = null; }
    if (pageId === 'page-network') loadNetworkConfig();
    if (pageId === 'page-plugins') loadPlugins();
    if (pageId === 'page-logs') initLogWebSocket(); 
}

// === API 请求 (System, AI, Net, Plugins) ===
async function checkSystem() {
    const box = document.getElementById('status-box'); box.innerText = '正在探测中枢 API...';
    try { const res = await fetch('/api/system/status'); const data = await res.json(); box.innerHTML = `<span class="log-info">[SYSTEM INFO]</span>\n${JSON.stringify(data, null, 2)}`;
    } catch (e) { box.innerHTML = `<span class="log-error">[ERROR]</span> 系统接口掉线：${e.message}`; }
}
async function checkAI() {
    const box = document.getElementById('status-box'); box.innerText = '正在 PING 大模型...';
    try { const res = await fetch('/api/ai/status', {method: 'POST'}); const data = await res.json(); box.innerHTML = `<span class="log-success">[AI CORE OK]</span>\n${JSON.stringify(data, null, 2)}`;
    } catch (e) { box.innerHTML = `<span class="log-error">[ERROR]</span> 大模型未响应。`; }
}
async function loadNetworkConfig() {
    try { const res = await fetch('/api/config/network'); const data = await res.json(); document.getElementById('input-llama').value = data.llama_url || ""; document.getElementById('input-router').value = data.router_url || ""; } catch(e) {}
}
async function saveNetworkConfig() {
    const btn = document.getElementById('btn-save-net'); const msg = document.getElementById('save-msg'); btn.innerText = "⏳ 保存中...";
    try { const res = await fetch('/api/config/network', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({llama_url: document.getElementById('input-llama').value.trim(), router_url: document.getElementById('input-router').value.trim()}) });
        const data = await res.json(); if (data.status === 'success') { msg.className = "log-success"; msg.innerText = "✔️ " + data.message; } else { msg.className = "log-error"; msg.innerText = "❌ " + data.message; }
    } catch(e) { msg.className = "log-error"; msg.innerText = "❌ 网络请求失败"; }
    btn.innerText = "💾 保存配置到 .env"; setTimeout(() => { msg.innerText = ""; msg.className = ""; }, 3000);
}

// 插件管理
async function loadPlugins() {
    const list = document.getElementById('plugin-list');
    try {
        const res = await fetch('/api/plugins'); const data = await res.json(); list.innerHTML = "";
        data.plugins.forEach(p => {
            const isActive = p.status === 'active';
            const dotClass = isActive ? 'status-active' : 'status-disabled';
            const btnText = isActive ? '禁用模块' : '启用模块';
            const statusText = isActive ? 'ACTIVE' : 'DISABLED';
            const colorVar = isActive ? 'var(--log-success)' : 'var(--log-error)';
            const isCore = p.name === 'web_ui' || p.name === 'common_core';
            
            const deleteBtnHtml = isCore ? `<button class="glass-btn glass-btn-disabled" disabled>🔒 核心锁定</button>` : `<button class="glass-btn glass-btn-danger" onclick="openDeleteModal('${p.raw_name}')">🗑️ 销毁</button>`;

            list.innerHTML += `
                <div class="plugin-item glass-panel-inner">
                    <div class="plugin-info">
                        <div class="status-dot ${dotClass}"></div>
                        <span style="font-family:'Consolas',monospace; font-size:1.1rem; text-shadow:0 0 5px rgba(255,255,255,0.1); word-break: break-all;">${p.name}</span>
                        <span style="font-size:0.8rem; color:${colorVar}; border:1px solid ${colorVar}; padding:2px 6px; border-radius:4px; margin-left:10px; box-shadow:0 0 5px ${colorVar}; flex-shrink: 0;">${statusText}</span>
                    </div>
                    <div class="plugin-actions">
                        <button class="glass-btn" onclick="togglePlugin('${p.raw_name}', '${isActive ? 'disabled' : 'active'}')">${btnText}</button>
                        ${deleteBtnHtml}
                    </div>
                </div>`;
        });
    } catch(e) { list.innerHTML = "<div class='log-error' style='text-align:center; padding:20px;'>⚠️ 读取失败</div>"; }
}
async function togglePlugin(rawName, targetStatus) {
    try { await fetch('/api/plugins/toggle', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({raw_name: rawName, target_status: targetStatus}) }); document.getElementById('plugin-list').innerHTML = "<div class='log-info' style='text-align:center; padding:20px;'>🔄 正在重载...</div>"; setTimeout(() => { loadPlugins(); }, 2000); } catch(e) {}
}

// 弹窗
let currentPluginToDelete = null;
function openDeleteModal(rawName) { currentPluginToDelete = rawName; document.getElementById('delete-plugin-name').innerText = rawName.replace(/^_/, ""); document.getElementById('delete-modal').classList.add('show'); }
function closeDeleteModal() { currentPluginToDelete = null; document.getElementById('delete-modal').classList.remove('show'); }
async function executeDelete() {
    if (!currentPluginToDelete) return; const rawName = currentPluginToDelete; closeDeleteModal(); document.getElementById('plugin-list').innerHTML = "<div class='log-error' style='text-align:center; padding:20px;'>🗑️ 物理清除中...</div>";
    try { const res = await fetch('/api/plugins/delete', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({raw_name: rawName}) }); const data = await res.json(); if (data.status === 'success') { setTimeout(() => { loadPlugins(); }, 2000); } else { alert(data.msg); loadPlugins(); }
    } catch(e) { alert("网络请求失败"); loadPlugins(); }
}

// Zip 拖拽
document.addEventListener("DOMContentLoaded", () => {
    const dropZone = document.getElementById("drop-zone"); const dropMsg = document.getElementById("drop-msg"); const fileInput = document.getElementById("file-input");
    if (!dropZone) return;
    dropZone.addEventListener("click", () => fileInput.click());
    dropZone.addEventListener("dragover", (e) => { e.preventDefault(); dropZone.classList.add("dragover"); dropMsg.innerText = "放开鼠标立即安装！"; });
    dropZone.addEventListener("dragleave", () => { dropZone.classList.remove("dragover"); dropMsg.innerText = "点击或将 .zip 拖拽到此处热安装"; });
    dropZone.addEventListener("drop", (e) => { e.preventDefault(); dropZone.classList.remove("dragover"); if (e.dataTransfer.files.length > 0) handleFileUpload(e.dataTransfer.files[0]); });
    fileInput.addEventListener("change", (e) => { if (e.target.files.length > 0) handleFileUpload(e.target.files[0]); });
    async function handleFileUpload(file) {
        if (!file.name.endsWith(".zip")) { alert("请上传 .zip 压缩包！"); return; }
        dropMsg.innerText = "⏳ 正在解压并热载入内核...";
        const formData = new FormData(); formData.append("file", file);
        try { const res = await fetch('/api/plugins/upload', { method: 'POST', body: formData }); const data = await res.json(); if (data.status === 'success') { dropMsg.innerText = data.msg; setTimeout(() => { dropMsg.innerText = "拖拽 .zip 包到此处热安装"; loadPlugins(); }, 2000); } else { dropMsg.className = "log-error"; dropMsg.innerText = data.msg; }
        } catch(e) { dropMsg.className = "log-error"; dropMsg.innerText = "❌ 上传中断！"; }
    }
});

// 日志 WS
let autoScroll = true;
function toggleAutoScroll() { autoScroll = !autoScroll; const btn = document.getElementById('auto-scroll-btn'); if (autoScroll) { btn.innerText = "自动滚动: 开启"; btn.style.background = "rgba(var(--monet-rgb), 0.15)"; } else { btn.innerText = "自动滚动: 暂停"; btn.style.background = "rgba(191,97,106,0.3)"; } }
window.loadLogs = function() { if (ws) ws.close(); initLogWebSocket(); };
function initLogWebSocket() {
    const consoleBox = document.getElementById('log-console'); if(!consoleBox) return;
    consoleBox.innerHTML = '<span class="log-info">[SYSTEM] 建立 WebSocket 神经管道...</span>';
    ws = new WebSocket(`${window.location.protocol==='https:'?'wss:':'ws:'}//${window.location.host}/api/logs/ws`);
    ws.onmessage = function(event) {
        const data = JSON.parse(event.data);
        if (data.status === 'success') {
            document.getElementById('log-file-name').innerText = "读取: " + data.file;
            let html = data.logs.replace(/</g, "&lt;").replace(/>/g, "&gt;");
            html = html.replace(/SUCCESS/g, '<span class="log-success">SUCCESS</span>');
            html = html.replace(/INFO/g, '<span class="log-info">INFO</span>');
            html = html.replace(/WARNING/g, '<span class="log-warn">WARNING</span>');
            html = html.replace(/ERROR/g, '<span class="log-error">ERROR</span>');
            consoleBox.innerHTML = html; if (autoScroll) consoleBox.scrollTop = consoleBox.scrollHeight;
        }
    };
}