// ==========================================
// PRTS 终端控制台 - 核心逻辑脚本 (完全体 v10)
// ==========================================

// === 0. ⚙️ 全局设置初始化 ===
let uiSettings = { anim: true, glass: true };

function initSettings() {
    const saved = localStorage.getItem('prts_settings');
    if (saved) {
        uiSettings = JSON.parse(saved);
        document.getElementById('setting-anim').checked = uiSettings.anim;
        document.getElementById('setting-glass').checked = uiSettings.glass;
    }
    applySettingsToBody();
}

function toggleSetting(key, value) {
    uiSettings[key] = value;
    localStorage.setItem('prts_settings', JSON.stringify(uiSettings));
    applySettingsToBody();
}

function applySettingsToBody() {
    if (!uiSettings.anim) document.body.classList.add('no-anim'); else document.body.classList.remove('no-anim');
    if (!uiSettings.glass) document.body.classList.add('no-glass'); else document.body.classList.remove('no-glass');
}

// === 1. 🎨 莫奈取色引擎与本地壁纸管理 ===
function initMonetEngine(customSrc = null) {
    const savedBg = localStorage.getItem('prts_custom_bg');
    const bgUrl = customSrc || savedBg || './background/bg.png';
    document.body.style.backgroundImage = `url('${bgUrl}')`;
    const img = new Image(); img.crossOrigin = "Anonymous"; img.src = bgUrl;
    img.onload = () => {
        const canvas = document.createElement('canvas'); const ctx = canvas.getContext('2d');
        canvas.width = img.width; canvas.height = img.height; ctx.drawImage(img, 0, 0, img.width, img.height);
        try {
            const data = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
            let r=0, g=0, b=0, count=0;
            for (let i = 0; i < data.length; i += 400) {
                if (data[i] > 30 && data[i] < 230 && data[i+3] > 128) { r += data[i]; g += data[i+1]; b += data[i+2]; count++; }
            }
            if(count > 0) {
                r = Math.floor(r / count); g = Math.floor(g / count); b = Math.floor(b / count);
                const boost = 1.3; r = Math.min(255, Math.floor(r * boost)); g = Math.min(255, Math.floor(g * boost)); b = Math.min(255, Math.floor(b * boost));
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
    localStorage.removeItem('prts_custom_bg'); initMonetEngine('./background/bg.jpg');
    const msg = document.getElementById('bg-upload-msg');
    if(msg) { msg.style.color = "var(--log-info)"; msg.innerText = "✔️ 已恢复默认"; setTimeout(()=>msg.innerText="", 3000); }
}

function initInteractiveLighting() {
    const panels = document.querySelectorAll('[data-interactive="true"]');
    if (panels.length === 0) return;
    document.addEventListener("mousemove", (event) => {
        if (!uiSettings.anim) return; // 关闭动画时停止计算
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
        const file = e.target.files[0]; if (!file) return;
        msg.style.color = "var(--log-warn)"; msg.innerText = "⏳ 正在压缩...";
        const reader = new FileReader();
        reader.onload = (evt) => {
            const img = new Image();
            img.onload = () => {
                const canvas = document.createElement('canvas'); let w = img.width; let h = img.height; const MAX_SIZE = 1920; 
                if (w > MAX_SIZE || h > MAX_SIZE) { if (w > h) { h = Math.round((h *= MAX_SIZE / w)); w = MAX_SIZE; } else { w = Math.round((w *= MAX_SIZE / h)); h = MAX_SIZE; } }
                canvas.width = w; canvas.height = h;
                const ctx = canvas.getContext('2d'); ctx.drawImage(img, 0, 0, w, h);
                const compressedDataUrl = canvas.toDataURL('image/jpeg', 0.8);
                try { localStorage.setItem('prts_custom_bg', compressedDataUrl); initMonetEngine(compressedDataUrl); msg.style.color = "var(--log-success)"; msg.innerText = "✔️ 壁纸已保存！"; } 
                catch(err) { msg.style.color = "var(--log-error)"; msg.innerText = "❌ 图片过大"; }
                setTimeout(()=>msg.innerText="", 4000);
            };
            img.src = evt.target.result;
        };
        reader.readAsDataURL(file);
    });
}

document.addEventListener("DOMContentLoaded", () => {
    initSettings();
    initMonetEngine();
    initInteractiveLighting();
    initBackgroundUpload();
});

// === 2. 🌗 主题切换 ===
let isDarkTheme = true;
let isTransitioning = false;

function performThemeSwitch() {
    const body = document.body; const themeBtn = document.getElementById('theme-btn');
    isDarkTheme = !isDarkTheme;
    if (isDarkTheme) { body.classList.add('dark-theme'); themeBtn.innerHTML = '☀️'; } 
    else { body.classList.remove('dark-theme'); themeBtn.innerHTML = '🌙'; }
}

async function toggleTheme(event) {
    if (isTransitioning) return;
    if (!document.startViewTransition || !uiSettings.anim) { performThemeSwitch(); return; } // 降级处理
    
    isTransitioning = true;
    const btn = event.currentTarget; const rect = btn.getBoundingClientRect();
    const x = rect.left + rect.width / 2; const y = rect.top + rect.height / 2;
    const endRadius = Math.hypot(Math.max(x, window.innerWidth - x), Math.max(y, window.innerHeight - y));
    document.documentElement.classList.add('theme-transitioning');
    
    const transition = document.startViewTransition(() => { performThemeSwitch(); });
    await transition.ready;
    const start = performance.now();
    function animateMask(time) {
        let progress = (time - start) / 700; if (progress > 1) progress = 1;
        const easeOut = 1 - Math.pow(1 - progress, 4); let currentRadius = endRadius * easeOut;
        if (currentRadius < 30) currentRadius = 30; 
        document.documentElement.style.setProperty('--mask-x', x + 'px'); document.documentElement.style.setProperty('--mask-y', y + 'px'); document.documentElement.style.setProperty('--mask-radius', currentRadius + 'px');
        if (progress < 1) requestAnimationFrame(animateMask); else { document.documentElement.classList.remove('theme-transitioning'); isTransitioning = false; }
    }
    requestAnimationFrame(animateMask);
}

// === 3. 📱 移动端菜单与导航 ===
function toggleMobileMenu() {
    const sidebar = document.getElementById('sidebar'); const overlay = document.getElementById('mobile-overlay');
    if (sidebar.classList.contains('mobile-open')) { sidebar.classList.remove('mobile-open'); overlay.classList.remove('show'); } 
    else { sidebar.classList.add('mobile-open'); overlay.classList.add('show'); }
}

let ws = null;
function switchTab(pageId, element, title) {
    document.querySelectorAll('.menu-item').forEach(item => item.classList.remove('active')); element.classList.add('active');
    const topbarTitle = document.getElementById('topbar-title'); if(topbarTitle) topbarTitle.innerText = title;
    document.querySelectorAll('.page-container').forEach(page => page.classList.remove('active')); document.getElementById(pageId).classList.add('active');
    if (window.innerWidth <= 768) toggleMobileMenu();
    if (ws) { ws.close(); ws = null; }
    if (pageId === 'page-env') loadEnvConfig();
    if (pageId === 'page-plugins') loadPlugins();
    if (pageId === 'page-logs') initLogWebSocket(); 
}

// === API 请求 ===
async function checkSystem() { const box = document.getElementById('status-box'); box.innerText = '正在探测...'; try { const res = await fetch('/api/system/status'); box.innerHTML = `<span class="log-info">[SYSTEM]</span>\n${JSON.stringify(await res.json(), null, 2)}`; } catch (e) { box.innerHTML = `<span class="log-error">[ERROR]</span> ${e.message}`; } }
async function checkAI() { const box = document.getElementById('status-box'); box.innerText = 'PING 大模型...'; try { const res = await fetch('/api/ai/status', {method: 'POST'}); box.innerHTML = `<span class="log-success">[AI CORE]</span>\n${JSON.stringify(await res.json(), null, 2)}`; } catch (e) { box.innerHTML = `<span class="log-error">[ERROR]</span> 未响应`; } }
// === 4. 🎛️ 全局 .env 环境配置动态管理器 ===
let currentEnvConfig = {};

async function loadEnvConfig() {
    try {
        const res = await fetch('/api/config/env');
        const data = await res.json();
        if (data.status === 'success') {
            currentEnvConfig = data.data;
            renderEnvConfig();
        }
    } catch(e) {
        document.getElementById('env-list-container').innerHTML = "<div class='log-error'>解析 .env 配置文件失败！</div>";
    }
}

// 智能渲染引擎
function renderEnvConfig() {
    const container = document.getElementById('env-list-container');
    container.innerHTML = '';
    
    // 如果文件是空的
    if (Object.keys(currentEnvConfig).length === 0) {
        container.innerHTML = "<div style='color:var(--text-muted); text-align:center; padding: 20px;'>配置文件暂无数据，请点击上方新增。</div>";
        return;
    }

    for (const [key, val] of Object.entries(currentEnvConfig)) {
        // 🌟 智能控件判定：如果是布尔值，渲染为丝滑的开关
        const isBool = (val.toLowerCase() === 'true' || val.toLowerCase() === 'false');
        let inputHtml = '';
        
        if (isBool) {
            const isChecked = val.toLowerCase() === 'true' ? 'checked' : '';
            inputHtml = `
                <label class="switch" style="margin-top:0;">
                    <input type="checkbox" onchange="updateEnvVal('${key}', this.checked ? 'true' : 'false')" ${isChecked}>
                    <span class="slider round"></span>
                </label>
            `;
        } else {
            // 普通字符串，处理引号转义防注入
            const safeVal = val.replace(/'/g, "&#39;").replace(/"/g, "&quot;");
            inputHtml = `<input type="text" class="glass-input" value="${safeVal}" onchange="updateEnvVal('${key}', this.value)" placeholder="输入变量值...">`;
        }

        container.innerHTML += `
            <div class="env-row">
                <div class="env-key">${key}</div>
                <div class="env-val">${inputHtml}</div>
                <button class="env-del-btn" onclick="deleteEnvVar('${key}')" title="永久删除此变量">🗑️</button>
            </div>
        `;
    }
}

// 值更新绑定
window.updateEnvVal = function(key, val) {
    currentEnvConfig[key] = val;
}

// 删除变量
window.deleteEnvVar = function(key) {
    if (confirm(`[ 危险操作 ]\n\n确定要从 .env 中永久删除环境变量 【 ${key} 】 吗？\n该操作会导致依赖此变量的插件无法运行。`)) {
        delete currentEnvConfig[key];
        renderEnvConfig(); // 重新渲染 UI
    }
}

// === 🎛️ 优雅的新增变量弹窗逻辑 ===
window.addNewEnvVar = function() {
    // 清空上次输入残留
    document.getElementById('new-env-key').value = '';
    document.getElementById('new-env-val').value = '';
    // 呼出定制弹窗
    document.getElementById('add-env-modal').classList.add('show');
    // 自动聚焦第一个输入框
    setTimeout(() => document.getElementById('new-env-key').focus(), 100);
}

window.closeAddEnvModal = function() {
    document.getElementById('add-env-modal').classList.remove('show');
}

window.confirmAddEnvVar = function() {
    const keyInput = document.getElementById('new-env-key').value.trim();
    const valInput = document.getElementById('new-env-val').value.trim();
    
    // 规范化键名：大写且只允许字母数字下划线
    const cleanKey = keyInput.toUpperCase().replace(/[^A-Z0-9_]/g, ""); 
    
    if (!cleanKey) {
        alert("键名不合法！只能包含字母、数字和下划线。");
        document.getElementById('new-env-key').focus();
        return;
    }
    
    if (currentEnvConfig[cleanKey] !== undefined) {
        alert("⚠️ 该变量已存在于列表中！");
        document.getElementById('new-env-key').focus();
        return;
    }
    
    // 插入新变量并刷新列表
    currentEnvConfig[cleanKey] = valInput;
    closeAddEnvModal();
    renderEnvConfig();
}

// 全量保存回写
async function saveEnvConfig() {
    const btn = document.getElementById('btn-save-env');
    const msg = document.getElementById('save-env-msg');
    btn.innerText = "⏳ 覆写文件深层数据中...";
    try {
        const res = await fetch('/api/config/env', { 
            method: 'POST', 
            headers: {'Content-Type': 'application/json'}, 
            body: JSON.stringify({config: currentEnvConfig}) 
        });
        const data = await res.json();
        if (data.status === 'success') {
            msg.className = "log-success"; msg.innerText = "✔️ " + data.msg;
        } else {
            msg.className = "log-error"; msg.innerText = "❌ " + data.msg;
        }
    } catch(e) {
        msg.className = "log-error"; msg.innerText = "❌ 网络传输异常";
    }
    btn.innerText = "💾 保存配置到 .env";
    setTimeout(() => { msg.innerText = ""; msg.className = ""; }, 3500);
}

// === 🌟 升级版插件管理 (接入 plugins.json) ===
async function loadPlugins() {
    const list = document.getElementById('plugin-list');
    try {
        const res = await fetch('/api/plugins'); 
        const data = await res.json(); 
        list.innerHTML = "";
        
        data.plugins.forEach(p => {
            const isActive = p.status === 'active';
            const dotClass = isActive ? 'status-active' : 'status-disabled';
            const btnText = isActive ? '禁用' : '启用';
            const statusColor = isActive ? 'var(--log-success)' : 'var(--log-error)';
            
            // 解析权限开关
            const toggleBtnHtml = p.can_disable ? 
                `<button class="glass-btn" onclick="togglePlugin('${p.raw_name}', '${isActive ? 'disabled' : 'active'}')">${btnText}</button>` : 
                `<button class="glass-btn glass-btn-disabled" disabled>🔒 防护</button>`;
                
            const deleteBtnHtml = p.can_delete ? 
                `<button class="glass-btn glass-btn-danger" onclick="openDeleteModal('${p.raw_name}')">🗑️ 销毁</button>` : 
                ``; // 不能删除则不显示按钮

            // 渲染复杂卡片
            list.innerHTML += `
                <div class="plugin-item glass-panel-inner">
                    <div class="plugin-info-main">
                        <div class="status-dot ${dotClass}"></div>
                        <div class="plugin-details">
                            <h4>${p.name_zh}</h4>
                            <div class="meta-tags">
                                <span class="meta-tag" style="color:${statusColor}; border-color:${statusColor};">${isActive ? 'ACTIVE' : 'DISABLED'}</span>
                                <span class="meta-tag">Dir: ${p.raw_name}</span>
                                <span class="meta-tag">Ver: ${p.version}</span>
                            </div>
                            <p class="plugin-desc">${p.description}</p>
                        </div>
                    </div>
                    <div class="plugin-actions">
                        ${toggleBtnHtml}
                        ${deleteBtnHtml}
                    </div>
                </div>`;
        });
    } catch(e) { list.innerHTML = "<div class='log-error' style='text-align:center; padding:20px;'>⚠️ 获取模块元数据失败</div>"; }
}

async function togglePlugin(rawName, targetStatus) {
    try { const res = await fetch('/api/plugins/toggle', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({raw_name: rawName, target_status: targetStatus}) }); const data = await res.json(); if(data.status==='error') alert(data.msg); document.getElementById('plugin-list').innerHTML = "<div class='log-info' style='text-align:center; padding:20px;'>🔄 重新编排节点中...</div>"; setTimeout(() => { loadPlugins(); }, 2000); } catch(e) {}
}

let currentPluginToDelete = null;
function openDeleteModal(rawName) { currentPluginToDelete = rawName; document.getElementById('delete-plugin-name').innerText = rawName.replace(/^_/, ""); document.getElementById('delete-modal').classList.add('show'); }
function closeDeleteModal() { currentPluginToDelete = null; document.getElementById('delete-modal').classList.remove('show'); }
async function executeDelete() {
    if (!currentPluginToDelete) return; const rawName = currentPluginToDelete; closeDeleteModal(); document.getElementById('plugin-list').innerHTML = "<div class='log-error' style='text-align:center; padding:20px;'>🗑️ 执行物理销毁...</div>";
    try { const res = await fetch('/api/plugins/delete', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({raw_name: rawName}) }); const data = await res.json(); if (data.status === 'success') { setTimeout(() => { loadPlugins(); }, 2000); } else { alert(data.msg); loadPlugins(); }
    } catch(e) { alert("网络请求失败"); loadPlugins(); }
}

// Zip
document.addEventListener("DOMContentLoaded", () => {
    const dropZone = document.getElementById("drop-zone"); const dropMsg = document.getElementById("drop-msg"); const fileInput = document.getElementById("file-input");
    if (!dropZone) return;
    dropZone.addEventListener("click", () => fileInput.click());
    dropZone.addEventListener("dragover", (e) => { e.preventDefault(); dropZone.classList.add("dragover"); dropMsg.innerText = "释放立即部署！"; });
    dropZone.addEventListener("dragleave", () => { dropZone.classList.remove("dragover"); dropMsg.innerText = "点击或将 .zip 拖拽到此处进行热安装"; });
    dropZone.addEventListener("drop", (e) => { e.preventDefault(); dropZone.classList.remove("dragover"); if (e.dataTransfer.files.length > 0) handleFileUpload(e.dataTransfer.files[0]); });
    fileInput.addEventListener("change", (e) => { if (e.target.files.length > 0) handleFileUpload(e.target.files[0]); });
    async function handleFileUpload(file) {
        if (!file.name.endsWith(".zip")) { alert("请上传 .zip 包"); return; }
        dropMsg.innerText = "⏳ 解压并注入内核..."; const formData = new FormData(); formData.append("file", file);
        try { const res = await fetch('/api/plugins/upload', { method: 'POST', body: formData }); const data = await res.json(); if (data.status === 'success') { dropMsg.innerText = data.msg; setTimeout(() => { dropMsg.innerText = "部署完成，请继续"; loadPlugins(); }, 2000); } else { dropMsg.className = "log-error"; dropMsg.innerText = data.msg; }
        } catch(e) { dropMsg.className = "log-error"; dropMsg.innerText = "❌ 传输中断"; }
    }
});

// 日志
let autoScroll = true;
function toggleAutoScroll() { autoScroll = !autoScroll; const btn = document.getElementById('auto-scroll-btn'); if (autoScroll) { btn.innerText = "自动滚动: 开启"; btn.style.background = "rgba(var(--monet-rgb), 0.15)"; } else { btn.innerText = "自动滚动: 暂停"; btn.style.background = "rgba(191,97,106,0.3)"; } }
window.loadLogs = function() { if (ws) ws.close(); initLogWebSocket(); };
function initLogWebSocket() {
    const consoleBox = document.getElementById('log-console'); if(!consoleBox) return;
    consoleBox.innerHTML = '<span class="log-info">[SYSTEM] 连接神经管道...</span>';
    ws = new WebSocket(`${window.location.protocol==='https:'?'wss:':'ws:'}//${window.location.host}/api/logs/ws`);
    ws.onmessage = function(event) {
        const data = JSON.parse(event.data);
        if (data.status === 'success') {
            document.getElementById('log-file-name').innerText = "流: " + data.file;
            let html = data.logs.replace(/</g, "&lt;").replace(/>/g, "&gt;");
            html = html.replace(/SUCCESS/g, '<span class="log-success">SUCCESS</span>');
            html = html.replace(/INFO/g, '<span class="log-info">INFO</span>');
            html = html.replace(/WARNING/g, '<span class="log-warn">WARNING</span>');
            html = html.replace(/ERROR/g, '<span class="log-error">ERROR</span>');
            consoleBox.innerHTML = html; if (autoScroll) consoleBox.scrollTop = consoleBox.scrollHeight;
        }
    };
}