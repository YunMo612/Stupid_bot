// ==========================================
// PRTS 终端控制台 - 核心逻辑脚本 (完全体)
// ==========================================


// === 1. 核心状态与主题切换 ===
let isDarkTheme = true;
let isTransitioning = false;

function performThemeSwitch() {
    const body = document.body;
    const themeBtn = document.getElementById('theme-btn');
    isDarkTheme = !isDarkTheme;
    if (isDarkTheme) {
        body.classList.remove('light-theme');
        themeBtn.innerHTML = '🌙 切换日间';
    } else {
        body.classList.add('light-theme');
        themeBtn.innerHTML = '🌌 切换夜间';
    }
}

async function toggleTheme(event) {
    if (isTransitioning) return;
    if (!document.startViewTransition) { performThemeSwitch(); return; }

    isTransitioning = true;
    const x = event.clientX;
    const y = event.clientY;
    const endRadius = Math.hypot(Math.max(x, window.innerWidth - x), Math.max(y, window.innerHeight - y));

    document.documentElement.classList.add('theme-transitioning');
    const transition = document.startViewTransition(() => { performThemeSwitch(); });

    await transition.ready;
    const start = performance.now();
    const duration = 600; 

    function animateMask(time) {
        let progress = (time - start) / duration;
        if (progress > 1) progress = 1;
        const easeOut = 1 - Math.pow(1 - progress, 4);
        const currentRadius = endRadius * easeOut;

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
// 定义一个全局变量，用来控制日志的定时刷新
let logInterval = null;

function switchTab(pageId, element, title) {
    document.querySelectorAll('.menu-item').forEach(item => item.classList.remove('active'));
    element.classList.add('active');
    document.getElementById('topbar-title').innerText = title;
    
    document.querySelectorAll('.page-container').forEach(page => page.classList.remove('active'));
    document.getElementById(pageId).classList.add('active');
    
    // 清理旧的定时器，防止在其他页面还在后台狂刷日志
    if (logInterval) {
        clearInterval(logInterval);
        logInterval = null;
    }
    
    // 按需加载数据
    if (pageId === 'page-network') loadNetworkConfig();
    if (pageId === 'page-plugins') loadPlugins();
    if (pageId === 'page-logs') {
        loadLogs(); // 立即加载一次
        logInterval = setInterval(loadLogs, 3000); // 开启 3 秒轮询
    }
}

// === 3. 系统与大模型监控 API ===
async function checkSystem() {
    const box = document.getElementById('status-box');
    box.innerText = '正在请求系统 API...';
    try {
        const res = await fetch('/api/system/status');
        const data = await res.json();
        box.innerHTML = `<span style="color:#81a1c1;">[SYSTEM INFO]</span>\n${JSON.stringify(data, null, 2)}`;
    } catch (e) {
        box.innerHTML = `<span style="color:#bf616a;">[ERROR]</span> 系统接口掉线：${e.message}`;
    }
}

async function checkAI() {
    const box = document.getElementById('status-box');
    box.innerText = '正在 PING 大模型核心节点...';
    try {
        const res = await fetch('/api/ai/status', {method: 'POST'});
        const data = await res.json();
        box.innerHTML = `<span style="color:#b48ead;">[AI CORE OK]</span>\n${JSON.stringify(data, null, 2)}`;
    } catch (e) {
        box.innerHTML = `<span style="color:#bf616a;">[ERROR]</span> 大模型节点未响应。请检查 prts_ai 模块是否加载。`;
    }
}

// === 4. 网络配置读取与保存 API ===
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
        const res = await fetch('/api/config/network', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({llama_url, router_url})
        });
        const data = await res.json();
        if (data.status === 'success') {
            msg.style.color = "#a3be8c";
            msg.innerText = "✔️ " + data.message;
        } else {
            msg.style.color = "#bf616a";
            msg.innerText = "❌ " + data.message;
        }
    } catch(e) {
        msg.style.color = "#bf616a";
        msg.innerText = "❌ 网络请求失败";
    }
    btn.innerText = "💾 保存配置到 .env";
    setTimeout(() => { msg.innerText = ""; }, 3000);
}

// === 5. 插件动态管理 API ===
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
            
            list.innerHTML += `
                <div class="plugin-item">
                    <div class="plugin-info">
                        <div class="status-dot ${dotClass}"></div>
                        <span style="color:var(--text-main); font-family: 'Consolas', monospace; font-size: 1.1rem;">${p.name}</span>
                        <span style="font-size: 0.8rem; color:${color}; border: 1px solid ${color}; padding: 2px 6px; border-radius: 4px;">${statusText}</span>
                    </div>
                    <button class="toggle-btn ${btnClass}" onclick="togglePlugin('${p.raw_name}', '${isActive ? 'disabled' : 'active'}')">${btnText}</button>
                </div>
            `;
        });
    } catch(e) { list.innerHTML = "<div style='color:#bf616a;'>读取列表失败</div>"; }
}

async function togglePlugin(rawName, targetStatus) {
    try {
        await fetch('/api/plugins/toggle', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({raw_name: rawName, target_status: targetStatus})
        });
        
        document.getElementById('plugin-list').innerHTML = "<div style='color:#ebcb8b; text-align:center; padding: 20px;'>🔄 底层引擎热重载中，请稍候...</div>";
        setTimeout(() => { loadPlugins(); }, 2000);
    } catch(e) { console.error("切换失败"); }
}

// === 6. Zip 插件拖拽上传系统 ===
document.addEventListener("DOMContentLoaded", () => {
    const dropZone = document.getElementById("drop-zone");
    const dropMsg = document.getElementById("drop-msg");
    const fileInput = document.getElementById("file-input");

    if (!dropZone) return; // 防止页面没加载完报错

    dropZone.addEventListener("click", () => fileInput.click());
    
    dropZone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropZone.classList.add("dragover");
        dropMsg.innerText = "放开鼠标立即安装！";
    });
    
    dropZone.addEventListener("dragleave", () => {
        dropZone.classList.remove("dragover");
        dropMsg.innerText = "将包含 __init__.py 的插件 .zip 包拖拽到此处进行热安装";
    });
    
    dropZone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropZone.classList.remove("dragover");
        if (e.dataTransfer.files.length > 0) handleFileUpload(e.dataTransfer.files[0]);
    });
    
    fileInput.addEventListener("change", (e) => {
        if (e.target.files.length > 0) handleFileUpload(e.target.files[0]);
    });

    async function handleFileUpload(file) {
        if (!file.name.endsWith(".zip")) {
            alert("请上传 .zip 压缩包！"); return;
        }
        
        dropMsg.style.color = "#ebcb8b";
        dropMsg.innerText = "⏳ 正在传输并解压到内核...";
        
        const formData = new FormData();
        formData.append("file", file);
        
        try {
            const res = await fetch('/api/plugins/upload', { method: 'POST', body: formData });
            const data = await res.json();
            
            if (data.status === 'success') {
                dropMsg.style.color = "#a3be8c";
                dropMsg.innerText = data.msg;
                setTimeout(() => { 
                    dropMsg.innerText = "将包含 __init__.py 的插件 .zip 包拖拽到此处进行热安装";
                    dropMsg.style.color = "";
                    loadPlugins(); 
                }, 2000);
            } else {
                dropMsg.style.color = "#bf616a";
                dropMsg.innerText = data.msg;
            }
        } catch(e) {
            dropMsg.style.color = "#bf616a";
            dropMsg.innerText = "❌ 上传网络中断！";
        }
    }
});

// ==========================================
// 实时日志渲染系统 (高亮、自动滚动、轮询)
// ==========================================
let autoScroll = true;

function toggleAutoScroll() {
    autoScroll = !autoScroll;
    const btn = document.getElementById('auto-scroll-btn');
    if (autoScroll) {
        btn.innerText = "自动滚动: 开启";
        btn.className = "toggle-btn btn-disable"; // 红色状态
    } else {
        btn.innerText = "自动滚动: 暂停";
        btn.className = "toggle-btn btn-enable";  // 绿色状态
    }
}

async function loadLogs() {
    try {
        const res = await fetch('/api/logs/latest');
        const data = await res.json();
        const consoleBox = document.getElementById('log-console');
        
        if (data.status === 'success') {
            document.getElementById('log-file-name').innerText = "读取文件: " + data.file;
            
            // 基础防错位替换
            let html = data.logs.replace(/</g, "&lt;").replace(/>/g, "&gt;");
            
            // 🌟 核心：为不同级别的日志注入颜色 CSS，实现终端级高亮！
            html = html.replace(/SUCCESS/g, '<span style="color: #a3be8c; font-weight: bold;">SUCCESS</span>');
            html = html.replace(/INFO/g, '<span style="color: #81a1c1; font-weight: bold;">INFO</span>');
            html = html.replace(/WARNING/g, '<span style="color: #ebcb8b; font-weight: bold;">WARNING</span>');
            html = html.replace(/ERROR/g, '<span style="color: #bf616a; font-weight: bold;">ERROR</span>');
            html = html.replace(/Traceback \(most recent call last\):/g, '<span style="color: #bf616a; text-decoration: underline;">Traceback (most recent call last):</span>');
            
            consoleBox.innerHTML = html;
        } else {
            consoleBox.innerText = data.logs;
        }

        // 判断是否需要自动滚动到最底部
        if (autoScroll) {
            consoleBox.scrollTop = consoleBox.scrollHeight;
        }
    } catch(e) {
        console.error("日志读取失败", e);
    }
}