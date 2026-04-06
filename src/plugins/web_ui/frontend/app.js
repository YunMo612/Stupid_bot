// ==========================================
// PRTS 终端控制台 - 核心逻辑脚本 (稳定版 v18 - 彻底修复异步生命周期死锁)
// ==========================================

let uiSettings = { anim: true, glass: true, md3: false, animSpeed: 1 };
let ws = null;
// ==========================================
// 🚀 核心：全局启动引擎 (代替原先失效的 DOMContentLoaded)
// ==========================================
function bootstrapPRTS() {
    console.log("[PRTS] 核心引擎启动中...");
    initSettings();
    
    // 注入预加载与模糊 Canvas DOM，独立接管背景渲染
    if (!document.getElementById('prts-background-loader')) {
        const loaderDiv = document.createElement('div');
        loaderDiv.id = 'prts-background-loader';
        loaderDiv.innerHTML = `
            <canvas id="blur-canvas" style="position:fixed;top:0;left:0;width:100%;height:100%;z-index:-2;filter:blur(30px) brightness(0.7);transition:opacity 0.8s ease;opacity:1;"></canvas>
            <div id="origin-bg" style="position:fixed;top:0;left:0;width:100%;height:100%;z-index:-1;transition:opacity 0.8s ease;opacity:0;background-size:cover;background-position:center;"></div>
        `;
        document.body.prepend(loaderDiv);
    }

    initMonetEngine();
    initInteractiveLighting();
    initBackgroundUpload();
    setTimeout(initMenuIndicator, 50); 
    
    // 初始化 ZIP 拖拽上传引擎
    initZipDropZone();
}

// 🌟 解决异步加载导致的生命周期错过问题
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bootstrapPRTS);
} else {
    bootstrapPRTS(); // 如果脚本异步加载完时 DOM 已经就绪，直接强行启动！
}

window.addEventListener('resize', () => {
    const activeItem = document.querySelector('.menu-item.active');
    if (activeItem) updateIndicator(activeItem, true);
});

function initSettings() {
    const saved = localStorage.getItem('prts_settings');
    if (saved) {
        uiSettings = JSON.parse(saved);
        if (document.getElementById('setting-anim')) document.getElementById('setting-anim').checked = uiSettings.anim;
        if (document.getElementById('setting-glass')) document.getElementById('setting-glass').checked = uiSettings.glass;
        if (document.getElementById('setting-md3')) document.getElementById('setting-md3').checked = !!uiSettings.md3;
        if (document.getElementById('setting-anim-speed')) document.getElementById('setting-anim-speed').value = uiSettings.animSpeed || 1;
    }
    applySettingsToBody();
}

window.toggleSetting = function(key, value) {
    uiSettings[key] = value;
    localStorage.setItem('prts_settings', JSON.stringify(uiSettings));
    applySettingsToBody();
    if (!uiSettings.md3) setTimeout(initMenuIndicator, 100); 
}

window.resetAllSettings = function() {
    localStorage.removeItem('prts_settings');
    localStorage.removeItem('prts_custom_bg');
    window.location.reload(); 
}

function applySettingsToBody() {
    if (!uiSettings.anim) document.body.classList.add('no-anim'); 
    else document.body.classList.remove('no-anim');
    
    if (!uiSettings.glass) document.body.classList.add('no-glass'); 
    else document.body.classList.remove('no-glass');

    const cssLink = document.getElementById('main-style');
    if (cssLink) {
        const targetCss = uiSettings.md3 ? './style_md.css' : './style.css';
        if (!cssLink.href.includes(targetCss.replace('./', ''))) {
            cssLink.href = `${targetCss}?t=${new Date().getTime()}`;
        }
    }
}

function initMenuIndicator() {
    const activeItem = document.querySelector('.menu-item.active');
    if (activeItem) updateIndicator(activeItem, true);
}

function updateIndicator(targetEl, isInit = false) {
    if (uiSettings.md3) return; 
    
    const indicator = document.getElementById('menu-indicator');
    const menu = targetEl.closest('.menu');
    if (!indicator || !menu) return;
    
    const currentTop = parseFloat(indicator.style.top || 0);
    const targetTop = targetEl.offsetTop;
    const targetBottom = menu.clientHeight - (targetEl.offsetTop + targetEl.offsetHeight);
    
    if (isInit || !uiSettings.anim) {
        indicator.style.transition = 'none';
        indicator.style.top = targetTop + 'px';
        indicator.style.bottom = targetBottom + 'px';
        indicator.offsetHeight; 
    } else {
        const isMovingDown = targetTop > currentTop;
        const ease = 'cubic-bezier(0.2, 0, 0, 1)';
        const mult = parseFloat(uiSettings.animSpeed) || 1;
        const dur = 0.25 * mult;
        
        if (isMovingDown) {
            indicator.style.transition = `top ${dur}s ${ease} ${dur}s, bottom ${dur}s ${ease} 0s`;
        } else {
            indicator.style.transition = `top ${dur}s ${ease} 0s, bottom ${dur}s ${ease} ${dur}s`;
        }
        
        indicator.style.top = targetTop + 'px';
        indicator.style.bottom = targetBottom + 'px';
    }
}

window.switchTab = function(pageId, element, icon, title) {
    document.querySelectorAll('.menu-item').forEach(item => item.classList.remove('active')); 
    element.classList.add('active');
    updateIndicator(element);
    
    const topbarTitle = document.getElementById('topbar-title'); 
    if(topbarTitle) topbarTitle.innerHTML = `<span class="material-symbols-outlined">${icon}</span> ${title}`;
    
    document.querySelectorAll('.page-container').forEach(page => page.classList.remove('active')); 
    document.getElementById(pageId).classList.add('active');
    
    if (window.innerWidth <= 768) toggleMobileMenu();
    if (ws) { ws.close(); ws = null; }
    
    if (pageId === 'page-env') loadEnvConfig();
    if (pageId === 'page-plugins') loadPlugins();
    if (pageId === 'page-logs') initLogWebSocket(); 
}

let isDarkTheme = true;
let isTransitioning = false;

function performThemeSwitch() {
    const body = document.body; const themeIcon = document.querySelector('#theme-btn .material-symbols-outlined');
    isDarkTheme = !isDarkTheme;
    if (isDarkTheme) { body.classList.add('dark-theme'); if (themeIcon) themeIcon.innerText = 'light_mode'; } 
    else { body.classList.remove('dark-theme'); if (themeIcon) themeIcon.innerText = 'dark_mode'; }
}

window.toggleTheme = async function(event) {
    if (isTransitioning) return;
    if (!document.startViewTransition || !uiSettings.anim) { performThemeSwitch(); return; } 
    isTransitioning = true; const btn = event.currentTarget; const rect = btn.getBoundingClientRect();
    const x = rect.left + rect.width / 2; const y = rect.top + rect.height / 2; const endRadius = Math.hypot(Math.max(x, window.innerWidth - x), Math.max(y, window.innerHeight - y));
    document.documentElement.classList.add('theme-transitioning');
    
    const transition = document.startViewTransition(() => { performThemeSwitch(); }); await transition.ready; const start = performance.now();
    const mult = parseFloat(uiSettings.animSpeed) || 1;
    const animDuration = 700 * mult;

    function animateMask(time) {
        let progress = (time - start) / animDuration; if (progress > 1) progress = 1;
        const easeOut = 1 - Math.pow(1 - progress, 4); let currentRadius = endRadius * easeOut; if (currentRadius < 30) currentRadius = 30; 
        document.documentElement.style.setProperty('--mask-x', x + 'px'); document.documentElement.style.setProperty('--mask-y', y + 'px'); document.documentElement.style.setProperty('--mask-radius', currentRadius + 'px');
        if (progress < 1) requestAnimationFrame(animateMask); else { document.documentElement.classList.remove('theme-transitioning'); isTransitioning = false; }
    }
    requestAnimationFrame(animateMask);
}

// ==========================================
// 🎨 T0级核心引擎：渐进式物理抖动加载与莫奈取色
// ==========================================
function initMonetEngine(customSrc = null) {
    const savedBg = localStorage.getItem('prts_custom_bg');
    
    // 🌟 修复：强制使用相对路径 ./ 免疫所有路由挂载点问题
    const defaultOrigin = './background/bg.png?v=' + new Date().getTime();
    const defaultBlur = './background/bg.png?v=' + new Date().getTime(); 
    
    const bgUrlOrigin = customSrc || savedBg || defaultOrigin;
    const bgUrlBlur = (customSrc || savedBg) ? bgUrlOrigin : defaultBlur; 

    const blurCanvas = document.getElementById('blur-canvas');
    const originBg = document.getElementById('origin-bg');
    if(!blurCanvas || !originBg) return;

    originBg.style.opacity = '0';
    blurCanvas.style.opacity = '1';
    blurCanvas.style.filter = 'blur(30px) brightness(0.7)';
    
    const imgBlur = new Image(); 
    imgBlur.src = bgUrlBlur;
    
    imgBlur.onload = () => {
        const ctx = blurCanvas.getContext('2d');
        blurCanvas.width = 192; 
        blurCanvas.height = 108;
        ctx.drawImage(imgBlur, 0, 0, blurCanvas.width, blurCanvas.height);
        
        try {
            const data = ctx.getImageData(0, 0, blurCanvas.width, blurCanvas.height).data;
            let r=0, g=0, b=0, count=0;
            for (let i = 0; i < data.length; i += 20) {
                if (data[i] > 30 && data[i] < 230 && data[i+3] > 128) { r += data[i]; g += data[i+1]; b += data[i+2]; count++; }
            }
            if(count > 0) {
                r = Math.floor(r / count); g = Math.floor(g / count); b = Math.floor(b / count);
                const boost = 1.3; 
                r = Math.min(255, Math.floor(r * boost)); g = Math.min(255, Math.floor(g * boost)); b = Math.min(255, Math.floor(b * boost));
                document.documentElement.style.setProperty('--monet-rgb', `${r}, ${g}, ${b}`);
            }
        } catch(e) { console.log("取色受限，使用默认主题色。"); }

        const imgOrigin = new Image();
        imgOrigin.src = bgUrlOrigin;
        imgOrigin.onload = () => {
            originBg.style.backgroundImage = `url('${bgUrlOrigin}')`;
            if (!uiSettings.anim) {
                originBg.style.opacity = '1'; blurCanvas.style.opacity = '0'; return;
            }
            performJitterTransition(blurCanvas, originBg);
        };
    };
    
    imgBlur.onerror = () => {
        console.error("图片加载失败！路径: " + bgUrlBlur);
        if (customSrc || savedBg) {
            localStorage.removeItem('prts_custom_bg'); initMonetEngine();
        } else {
            document.body.style.backgroundImage = "linear-gradient(135deg, #0f1016, #212436)";
            document.documentElement.style.setProperty('--monet-rgb', '100, 150, 255');
            blurCanvas.style.opacity = '0'; originBg.style.opacity = '0';
        }
    };
}

function performJitterTransition(canvas, originBg) {
    const mult = parseFloat(uiSettings.animSpeed) || 1;
    const dur = 800 * mult; 
    const jitterStr = 12 * mult; 
    
    originBg.style.transition = `opacity ${dur}ms ease, transform ${dur}ms cubic-bezier(0.18, 0.89, 0.32, 1.28)`;
    canvas.style.transition = `opacity ${dur}ms ease, filter ${dur}ms ease`;
    originBg.style.transform = `scale(1.05) translate(${jitterStr}px, -${jitterStr}px) translateZ(0)`;
    
    requestAnimationFrame(() => {
        originBg.style.opacity = '1';
        canvas.style.filter = 'blur(60px) brightness(0.6)';
        canvas.style.opacity = '0';
        originBg.style.transform = 'scale(1) translate(0, 0) translateZ(0)';
    });
}

window.resetBackground = function() {
    localStorage.removeItem('prts_custom_bg'); initMonetEngine(); 
    const msg = document.getElementById('bg-upload-msg');
    if(msg) { msg.style.color = "var(--log-info)"; msg.innerText = "✔️ 已恢复默认"; setTimeout(() => msg.innerText="", 3000); }
}

function initInteractiveLighting() {
    const panels = document.querySelectorAll('[data-interactive="true"]'); if (panels.length === 0) return;
    document.addEventListener("mousemove", (event) => {
        if (!uiSettings.anim) return; 
        panels.forEach((panel) => { const rect = panel.getBoundingClientRect(); panel.style.setProperty('--light-x', `${event.clientX - rect.left}px`); panel.style.setProperty('--light-y', `${event.clientY - rect.top}px`); });
    });
}

function initBackgroundUpload() {
    const bgUpload = document.getElementById('bg-upload'); const msg = document.getElementById('bg-upload-msg'); if (!bgUpload) return;
    bgUpload.addEventListener('change', function(e) {
        const file = e.target.files[0]; if (!file) return; msg.style.color = "var(--log-warn)"; msg.innerText = "⏳ 正在压缩...";
        const reader = new FileReader();
        reader.onload = (evt) => {
            const img = new Image();
            img.onload = () => {
                const canvas = document.createElement('canvas'); let w = img.width; let h = img.height; const MAX_SIZE = 1920; 
                if (w > MAX_SIZE || h > MAX_SIZE) { if (w > h) { h = Math.round((h *= MAX_SIZE / w)); w = MAX_SIZE; } else { w = Math.round((w *= MAX_SIZE / h)); h = MAX_SIZE; } }
                canvas.width = w; canvas.height = h; const ctx = canvas.getContext('2d'); ctx.drawImage(img, 0, 0, w, h); const compressedDataUrl = canvas.toDataURL('image/jpeg', 0.8);
                try { localStorage.setItem('prts_custom_bg', compressedDataUrl); initMonetEngine(compressedDataUrl); msg.style.color = "var(--log-success)"; msg.innerText = "✔️ 壁纸已保存！"; } 
                catch(err) { msg.style.color = "var(--log-error)"; msg.innerText = "❌ 图片过大"; } setTimeout(() => msg.innerText="", 4000);
            }; img.src = evt.target.result;
        }; reader.readAsDataURL(file);
    });
}

function initZipDropZone() {
    const dropZone = document.getElementById("drop-zone"); const dropMsg = document.getElementById("drop-msg"); const fileInput = document.getElementById("file-input"); if (!dropZone) return;
    dropZone.addEventListener("click", () => fileInput.click()); dropZone.addEventListener("dragover", (e) => { e.preventDefault(); dropZone.classList.add("dragover"); dropMsg.innerText = "释放立即部署！"; }); dropZone.addEventListener("dragleave", () => { dropZone.classList.remove("dragover"); dropMsg.innerText = "点击或拖拽 .zip 包热安装"; }); dropZone.addEventListener("drop", (e) => { e.preventDefault(); dropZone.classList.remove("dragover"); if (e.dataTransfer.files.length > 0) handleFileUpload(e.dataTransfer.files[0]); });
    fileInput.addEventListener("change", (e) => { if (e.target.files.length > 0) handleFileUpload(e.target.files[0]); });
    async function handleFileUpload(file) {
        if (!file.name.endsWith(".zip")) { alert("请上传 .zip 包"); return; }
        dropMsg.innerText = "⏳ 注入内核..."; const formData = new FormData(); formData.append("file", file);
        try { 
            const res = await fetch('/api/plugins/upload', { method: 'POST', body: formData }); const data = await res.json(); 
            if (data.status === 'success') { dropMsg.innerText = data.msg; setTimeout(() => { dropMsg.innerText = "部署完成"; loadPlugins(); }, 2000); } else { dropMsg.className = "log-error"; dropMsg.innerText = data.msg; }
        } catch(e) { dropMsg.className = "log-error"; dropMsg.innerText = "❌ 传输中断"; }
    }
}

window.toggleMobileMenu = function() {
    const sidebar = document.getElementById('sidebar'); const overlay = document.getElementById('mobile-overlay');
    if (sidebar.classList.contains('mobile-open')) { sidebar.classList.remove('mobile-open'); overlay.classList.remove('show'); } 
    else { sidebar.classList.add('mobile-open'); overlay.classList.add('show'); }
}

window.checkSystem = async function() { const box = document.getElementById('status-box'); box.innerText = '正在探测...'; try { const res = await fetch('/api/system/status'); box.innerHTML = `<span class="log-info">[SYSTEM]</span>\n${JSON.stringify(await res.json(), null, 2)}`; } catch (e) { box.innerHTML = `<span class="log-error">[ERROR]</span> ${e.message}`; } }
window.checkAI = async function() { const box = document.getElementById('status-box'); box.innerText = 'PING 大模型...'; try { const res = await fetch('/api/ai/status', {method: 'POST'}); box.innerHTML = `<span class="log-success">[AI CORE]</span>\n${JSON.stringify(await res.json(), null, 2)}`; } catch (e) { box.innerHTML = `<span class="log-error">[ERROR]</span> 未响应`; } }

let deleteTimer = null;
function startDeleteCountdown(btnId, originalText) {
    const btn = document.getElementById(btnId); if (!btn) return;
    let count = 10; btn.disabled = true; btn.innerText = `${originalText} (${count}s)`; clearInterval(deleteTimer); 
    deleteTimer = setInterval(() => { count--; if (count > 0) { btn.innerText = `${originalText} (${count}s)`; } else { clearInterval(deleteTimer); btn.disabled = false; btn.innerText = originalText; } }, 1000);
}
function stopDeleteCountdown(btnId, originalText) { clearInterval(deleteTimer); const btn = document.getElementById(btnId); if(btn) { btn.disabled = true; btn.innerText = originalText; } }

let currentEnvConfig = {};
async function loadEnvConfig() { try { const res = await fetch('/api/config/env'); const data = await res.json(); if (data.status === 'success') { currentEnvConfig = data.data; renderEnvConfig(); } } catch(e) { document.getElementById('env-list-container').innerHTML = "<div class='log-error'>解析 .env 配置文件失败！</div>"; } }
function renderEnvConfig() {
    const container = document.getElementById('env-list-container'); container.innerHTML = '';
    if (Object.keys(currentEnvConfig).length === 0) { container.innerHTML = "<div style='color:var(--text-muted); text-align:center; padding: 20px;'>配置文件暂无数据，请点击上方新增。</div>"; return; }
    for (const [key, val] of Object.entries(currentEnvConfig)) {
        const isBool = (val.toLowerCase() === 'true' || val.toLowerCase() === 'false'); let inputHtml = '';
        if (isBool) { inputHtml = `<label class="switch" style="margin-top:0;"><input type="checkbox" onchange="window.updateEnvVal('${key}', this.checked ? 'true' : 'false')" ${val.toLowerCase() === 'true' ? 'checked' : ''}><span class="slider round"></span></label>`; } 
        else { inputHtml = `<input type="text" class="glass-input" value="${val.replace(/'/g, "&#39;").replace(/"/g, "&quot;")}" onchange="window.updateEnvVal('${key}', this.value)" placeholder="输入变量值...">`; }
        container.innerHTML += `<div class="env-row"><div class="env-key">${key}</div><div class="env-val">${inputHtml}</div><button class="env-del-btn" onclick="window.deleteEnvVar('${key}')" title="永久删除此变量"><span class="material-symbols-outlined">delete</span></button></div>`;
    }
}
window.updateEnvVal = function(key, val) { currentEnvConfig[key] = val; }
let currentEnvKeyToDelete = null;
window.deleteEnvVar = function(key) { currentEnvKeyToDelete = key; document.getElementById('env-delete-key').innerText = key; document.getElementById('env-delete-modal').classList.add('show'); startDeleteCountdown('btn-confirm-env', '确认删除'); }
window.closeEnvDeleteModal = function() { currentEnvKeyToDelete = null; document.getElementById('env-delete-modal').classList.remove('show'); stopDeleteCountdown('btn-confirm-env', '确认删除'); }
window.executeEnvDelete = function() { if (!currentEnvKeyToDelete) return; delete currentEnvConfig[currentEnvKeyToDelete]; window.closeEnvDeleteModal(); renderEnvConfig(); }

window.addNewEnvVar = function() { document.getElementById('new-env-key').value = ''; document.getElementById('new-env-val').value = ''; document.getElementById('add-env-modal').classList.add('show'); setTimeout(() => document.getElementById('new-env-key').focus(), 100); }
window.closeAddEnvModal = function() { document.getElementById('add-env-modal').classList.remove('show'); }
window.confirmAddEnvVar = function() {
    const keyInput = document.getElementById('new-env-key').value.trim(); const valInput = document.getElementById('new-env-val').value.trim();
    const cleanKey = keyInput.toUpperCase().replace(/[^A-Z0-9_]/g, ""); 
    if (!cleanKey) { alert("键名不合法！"); document.getElementById('new-env-key').focus(); return; }
    if (currentEnvConfig[cleanKey] !== undefined) { alert("⚠️ 该变量已存在！"); document.getElementById('new-env-key').focus(); return; }
    currentEnvConfig[cleanKey] = valInput; window.closeAddEnvModal(); renderEnvConfig();
}
window.saveEnvConfig = async function() {
    const btn = document.getElementById('btn-save-env'); const msg = document.getElementById('save-env-msg'); const originalText = btn.innerHTML;
    btn.innerHTML = `<span class="material-symbols-outlined" style="font-size: 18px; margin-right: 5px; vertical-align: middle;">sync</span>覆写文件中...`;
    try {
        const res = await fetch('/api/config/env', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({config: currentEnvConfig}) });
        const data = await res.json(); if (data.status === 'success') { msg.className = "log-success"; msg.innerText = "✔️ " + data.msg; } else { msg.className = "log-error"; msg.innerText = "❌ " + data.msg; }
    } catch(e) { msg.className = "log-error"; msg.innerText = "❌ 传输异常"; }
    btn.innerHTML = originalText; setTimeout(() => { msg.innerText = ""; msg.className = ""; }, 3500);
}

async function loadPlugins() {
    const list = document.getElementById('plugin-list');
    try {
        const res = await fetch('/api/plugins'); const data = await res.json(); list.innerHTML = "";
        data.plugins.forEach(p => {
            const isActive = p.status === 'active'; const dotClass = isActive ? 'status-active' : 'status-disabled'; const btnText = isActive ? '禁用' : '启用'; const statusColor = isActive ? 'var(--log-success)' : 'var(--log-error)';
            const toggleBtnHtml = p.can_disable ? `<button class="glass-btn" onclick="window.togglePlugin('${p.raw_name}', '${isActive ? 'disabled' : 'active'}')">${btnText}</button>` : `<button class="glass-btn glass-btn-disabled" disabled><span class="material-symbols-outlined" style="font-size:16px;vertical-align:middle;margin-right:4px;">lock</span>防护</button>`;
            const deleteBtnHtml = p.can_delete ? `<button class="glass-btn glass-btn-danger" onclick="window.openDeleteModal('${p.raw_name}')"><span class="material-symbols-outlined" style="font-size:16px;vertical-align:middle;margin-right:4px;">delete</span>销毁</button>` : ``; 
            list.innerHTML += `<div class="plugin-item glass-panel-inner"><div class="plugin-info-main"><div class="status-dot ${dotClass}"></div><div class="plugin-details"><h4>${p.name_zh}</h4><div class="meta-tags"><span class="meta-tag" style="color:${statusColor}; border-color:${statusColor};">${isActive ? 'ACTIVE' : 'DISABLED'}</span><span class="meta-tag">Dir: ${p.raw_name}</span><span class="meta-tag">Ver: ${p.version}</span></div><p class="plugin-desc">${p.description}</p></div></div><div class="plugin-actions">${toggleBtnHtml}${deleteBtnHtml}</div></div>`;
        });
    } catch(e) { list.innerHTML = "<div class='log-error' style='text-align:center; padding:20px;'>⚠️ 获取元数据失败</div>"; }
}

window.togglePlugin = async function(rawName, targetStatus) {
    try { 
        const res = await fetch('/api/plugins/toggle', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({raw_name: rawName, target_status: targetStatus}) }); 
        const data = await res.json(); if(data.status === 'error') alert(data.msg); 
        document.getElementById('plugin-list').innerHTML = "<div class='log-info' style='text-align:center; padding:20px;'>🔄 重新编排中...</div>"; setTimeout(() => { loadPlugins(); }, 2000); 
    } catch(e) {}
}

let currentPluginToDelete = null;
window.openDeleteModal = function(rawName) { currentPluginToDelete = rawName; document.getElementById('delete-plugin-name').innerText = rawName.replace(/^_/, ""); document.getElementById('delete-modal').classList.add('show'); startDeleteCountdown('btn-confirm-plugin', '确认销毁'); }
window.closeDeleteModal = function() { currentPluginToDelete = null; document.getElementById('delete-modal').classList.remove('show'); stopDeleteCountdown('btn-confirm-plugin', '确认销毁'); }
window.executeDelete = async function() {
    if (!currentPluginToDelete) return; window.closeDeleteModal(); document.getElementById('plugin-list').innerHTML = "<div class='log-error' style='text-align:center; padding:20px;'>🗑️ 执行物理销毁...</div>";
    try { 
        const res = await fetch('/api/plugins/delete', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({raw_name: currentPluginToDelete}) }); 
        const data = await res.json(); if (data.status === 'success') { setTimeout(() => { loadPlugins(); }, 2000); } else { alert(data.msg); loadPlugins(); }
    } catch(e) { alert("网络失败"); loadPlugins(); }
}

let autoScroll = true;
window.toggleAutoScroll = function() { 
    autoScroll = !autoScroll; const btn = document.getElementById('auto-scroll-btn'); 
    if (autoScroll) { btn.innerHTML = '<span class="material-symbols-outlined" style="font-size: 18px; vertical-align: middle;">swap_vert</span> 自动滚动: 开启'; btn.style.background = "rgba(var(--monet-rgb), 0.15)"; } 
    else { btn.innerHTML = '<span class="material-symbols-outlined" style="font-size: 18px; vertical-align: middle;">sync_disabled</span> 自动滚动: 暂停'; btn.style.background = "rgba(191,97,106,0.3)"; } 
}
window.loadLogs = function() { if (ws) ws.close(); initLogWebSocket(); };
function initLogWebSocket() {
    const consoleBox = document.getElementById('log-console'); if(!consoleBox) return;
    consoleBox.innerHTML = '<span class="log-info">[SYSTEM] 连接管道...</span>';
    ws = new WebSocket(`${window.location.protocol==='https:'?'wss:':'ws:'}//${window.location.host}/api/logs/ws`);
    ws.onmessage = function(event) {
        const data = JSON.parse(event.data);
        if (data.status === 'success') {
            document.getElementById('log-file-name').innerText = "流: " + data.file;
            let html = data.logs.replace(/</g, "&lt;").replace(/>/g, "&gt;");
            html = html.replace(/SUCCESS/g, '<span class="log-success">SUCCESS</span>'); html = html.replace(/INFO/g, '<span class="log-info">INFO</span>'); html = html.replace(/WARNING/g, '<span class="log-warn">WARNING</span>'); html = html.replace(/ERROR/g, '<span class="log-error">ERROR</span>');
            consoleBox.innerHTML = html; if (autoScroll) consoleBox.scrollTop = consoleBox.scrollHeight;
        }
    };
}