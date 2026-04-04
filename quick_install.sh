#!/usr/bin/env bash
# ==============================================================================
#  Stupid_Bot (mybot) 一键安装与启动脚本
#  技术栈: Python 3.10+ / NoneBot2 / FastAPI / OneBot V11
# ==============================================================================
set -Eeuo pipefail

# ====================== 颜色与日志 ======================
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[0;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

info()    { echo -e "${BLUE}[→]${NC} $*"; }
success() { echo -e "${GREEN}[✓]${NC} $*"; }
warn()    { echo -e "${YELLOW}[⚠]${NC} $*"; }
error()   { echo -e "${RED}[✗]${NC} $*" >&2; }
header()  { echo -e "\n${BOLD}${CYAN}══════ $* ══════${NC}\n"; }

# ====================== 项目路径 ======================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"
VENV_DIR="$PROJECT_DIR/.venv"
ENV_FILE="$PROJECT_DIR/.env"
BOT_DATA="$PROJECT_DIR/bot_data.json"
BOT_DATA_DEMO="$PROJECT_DIR/bot_data.demo.json"
BOT_PY="$PROJECT_DIR/bot.py"
MIN_PY_MAJOR=3
MIN_PY_MINOR=10
DEFAULT_PORT=8080

# ====================== 运行模式 ======================
MODE="full"
FORCE=false
PYTHON_CMD=""

usage() {
    cat <<EOF
Stupid_Bot 一键安装与启动脚本

用法: $(basename "$0") [选项]

选项:
  --install-only   仅安装依赖和初始化配置，不启动
  --start-only     跳过安装，直接启动（需已完成安装）
  --force          强制重建虚拟环境
  --help, -h       显示帮助

示例:
  ./$(basename "$0")                 完整安装并启动
  ./$(basename "$0") --install-only  只安装
  ./$(basename "$0") --start-only    只启动
  ./$(basename "$0") --force         强制重装依赖
EOF
    exit 0
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --install-only) MODE="install"; shift ;;
        --start-only)   MODE="start";   shift ;;
        --force)        FORCE=true;     shift ;;
        --help|-h)      usage ;;
        *)              error "未知参数: $1"; echo ""; usage ;;
    esac
done

# ====================== 错误捕获 ======================
on_exit() {
    local code=$?
    if [[ $code -ne 0 ]]; then
        echo ""
        error "脚本异常退出 (退出码: $code)"
        error "请检查上方错误信息"
    fi
}
trap on_exit EXIT

# ==============================================================================
#  Phase 0: 基础环境检查
# ==============================================================================
phase_check() {
    header "Phase 0/4 — 基础环境检查"

    # --- OS ---
    if [[ "$(uname -s)" != "Linux" ]]; then
        error "此脚本仅支持 Linux 系统"
        exit 1
    fi
    local os_id="" os_name="Linux"
    if [[ -f /etc/os-release ]]; then
        # shellcheck disable=SC1091
        os_id=$(. /etc/os-release && echo "${ID:-}")
        os_name=$(. /etc/os-release && echo "${PRETTY_NAME:-Linux}")
    fi
    info "操作系统: $os_name"

    # --- Python >= 3.10 ---
    for cmd in python3 python; do
        if command -v "$cmd" &>/dev/null; then
            local ver major minor
            ver=$("$cmd" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null) || continue
            major=${ver%%.*}; minor=${ver##*.}
            if (( major > MIN_PY_MAJOR || (major == MIN_PY_MAJOR && minor >= MIN_PY_MINOR) )); then
                PYTHON_CMD="$cmd"
                break
            fi
        fi
    done
    if [[ -z "$PYTHON_CMD" ]]; then
        error "需要 Python >= ${MIN_PY_MAJOR}.${MIN_PY_MINOR}"
        if [[ "$os_id" == "debian" || "$os_id" == "ubuntu" ]]; then
            info "安装: sudo apt update && sudo apt install python3 python3-venv python3-pip"
        fi
        exit 1
    fi
    success "Python: $("$PYTHON_CMD" --version 2>&1)"

    # --- python3-venv ---
    if ! "$PYTHON_CMD" -m venv -h &>/dev/null; then
        error "python3-venv 不可用"
        if [[ "$os_id" == "debian" || "$os_id" == "ubuntu" ]]; then
            info "安装: sudo apt install python3-venv"
        fi
        exit 1
    fi
    success "python3-venv: 可用"

    # --- pip ---
    if ! "$PYTHON_CMD" -m pip --version &>/dev/null; then
        error "pip 不可用"
        if [[ "$os_id" == "debian" || "$os_id" == "ubuntu" ]]; then
            info "安装: sudo apt install python3-pip"
        fi
        exit 1
    fi
    success "pip: 可用"

    # --- 入口文件 ---
    if [[ ! -f "$BOT_PY" ]]; then
        error "未找到 bot.py — 请确认脚本位于 mybot 项目根目录"
        exit 1
    fi
    success "入口文件: bot.py"
}

# ==============================================================================
#  Phase 1: 虚拟环境与依赖安装
# ==============================================================================
phase_deps() {
    header "Phase 1/4 — 虚拟环境与依赖安装"

    # --- 创建 / 重建 venv ---
    if [[ "$FORCE" == true && -d "$VENV_DIR" ]]; then
        warn "--force: 删除旧 .venv ..."
        rm -rf "$VENV_DIR"
    fi

    if [[ ! -d "$VENV_DIR" ]]; then
        info "创建虚拟环境 .venv ..."
        "$PYTHON_CMD" -m venv "$VENV_DIR" || {
            error "虚拟环境创建失败"; exit 2
        }
        success "虚拟环境已创建"
    else
        success "虚拟环境已存在，跳过创建"
    fi

    # --- 激活 ---
    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate"
    success "虚拟环境已激活"

    # --- 升级 pip ---
    info "升级 pip ..."
    python -m pip install --upgrade pip -q 2>/dev/null || true

    # --- 安装依赖 ---
    # 说明:
    #   pyproject.toml 仅声明了 nonebot2[fastapi] 和 nonebot-adapter-onebot，
    #   但代码中实际 import 了更多包（通过 grep 代码 + pip freeze 交叉确认）。
    #   仓库中不存在 requirements.txt（README 记载有误）。
    #   因此这里按实际需要显式安装全部直接依赖。

    info "安装核心框架 ..."
    python -m pip install -q \
        "nonebot2[fastapi]>=2.4.4" \
        "nonebot-adapter-onebot>=2.4.6" \
    || { error "核心依赖安装失败"; exit 3; }

    info "安装项目额外依赖 ..."
    python -m pip install -q \
        aiomysql \
        aiohttp \
        httpx \
        mcstatus \
        openai \
        duckduckgo_search \
        beautifulsoup4 \
        lxml \
    || { error "额外依赖安装失败"; exit 3; }

    # --- 关键包导入验证 ---
    local failed=0
    #        import名:显示名
    local checks=(
        "nonebot:nonebot2"
        "aiomysql:aiomysql"
        "aiohttp:aiohttp"
        "httpx:httpx"
        "mcstatus:mcstatus"
        "fastapi:fastapi"
        "uvicorn:uvicorn"
    )
    for item in "${checks[@]}"; do
        local mod="${item%%:*}" pkg="${item##*:}"
        if ! python -c "import $mod" &>/dev/null; then
            warn "包 $pkg (import $mod) 验证失败"
            ((failed++)) || true
        fi
    done

    local total
    total=$(python -m pip list --format=columns 2>/dev/null | tail -n +3 | wc -l) || total="?"
    if (( failed == 0 )); then
        success "依赖就绪 — 共 ${total} 个包，关键包全部通过"
    else
        warn "依赖安装完毕 — ${failed} 个包验证异常，可能影响运行"
    fi
}

# ==============================================================================
#  Phase 2: 配置文件初始化
# ==============================================================================
phase_config() {
    header "Phase 2/4 — 配置文件初始化"

    # ------ .env ------
    if [[ -f "$ENV_FILE" ]]; then
        success ".env 已存在，跳过生成"
        if grep -qE 'YOUR_QQ_NUMBER' "$ENV_FILE" 2>/dev/null; then
            warn ".env 中检测到未修改的占位符，请编辑"
        fi
    else
        info "生成 .env 配置模板 ..."
        cat > "$ENV_FILE" <<'ENVTEMPLATE'
# ==========================================================
#  Stupid_Bot 环境配置
#  请务必修改标注 [必填] 的项目
# ==========================================================

# [必填] NoneBot 驱动
DRIVER=~fastapi

# [必填] 超级管理员 QQ 号 (JSON 数组)
SUPERUSERS=["YOUR_QQ_NUMBER"]

# 指令前缀
COMMAND_START=["/", ""]

# Bot 监听地址与端口 (NapCat 反向 WS 需连接此端口)
HOST=0.0.0.0
PORT=8080

# 数据库 (MariaDB / MySQL)
# 如不使用皮肤站相关功能可留空
DB_HOST="127.0.0.1"
DB_PORT=3306
DB_USER=""
DB_PASS=""
DB_NAME=""

# [必填] LLM 大模型 API
LLAMA_SERVER_URL="http://127.0.0.1:11434/v1/chat/completions"
ROUTER_URL="http://127.0.0.1:11434/v1/chat/completions"

# TTS 语音合成 (可选)
MELOTTS_API_URL="http://127.0.0.1:8082"

# 运行时
LOCALSTORE_USE_CWD=true
ENVIRONMENT=dev
RELOAD=true
ENVTEMPLATE
        success ".env 模板已生成"
        echo ""
        warn "=========================================="
        warn "  请编辑 .env 填写以下必要配置:"
        warn ""
        warn "  1. SUPERUSERS       → 你的 QQ 号"
        warn "  2. LLAMA_SERVER_URL → LLM API 地址"
        warn "  3. DB_* 系列        → 数据库连接 (如需皮肤站功能)"
        warn ""
        warn "  编辑命令: nano $ENV_FILE"
        warn "=========================================="
        echo ""
    fi

    # ------ bot_data.json ------
    if [[ -f "$BOT_DATA" ]]; then
        success "bot_data.json 已存在"
    elif [[ -f "$BOT_DATA_DEMO" ]]; then
        cp "$BOT_DATA_DEMO" "$BOT_DATA"
        success "bot_data.json ← 从 bot_data.demo.json 复制"
    else
        # data_manager.py 会自动初始化，但预创建更干净
        cat > "$BOT_DATA" <<'DATAJSON'
{
    "admin_users": [],
    "dev_users": [],
    "claimed_users": [],
    "bind_users": {},
    "checkin_records": {}
}
DATAJSON
        success "bot_data.json 已生成 (空模板)"
    fi

    # ------ 其他 JSON 配置检查 ------
    for f in ai_config.json ai_prompt.json plugins.json; do
        if [[ -f "$PROJECT_DIR/$f" ]]; then
            success "$f ✓"
        else
            warn "$f 缺失 — 相关功能可能受影响"
        fi
    done

    # ------ 日志目录 ------
    mkdir -p "$PROJECT_DIR/logs"
    success "logs/ 目录就绪"
}

# ==============================================================================
#  Phase 3: 环境验证
# ==============================================================================

# 从 .env 中读取 PORT 值的辅助函数
get_port() {
    local port="$DEFAULT_PORT"
    if [[ -f "$ENV_FILE" ]]; then
        local p
        p=$(grep -oP '^\s*PORT\s*=\s*\K\d+' "$ENV_FILE" 2>/dev/null) || true
        [[ -n "$p" ]] && port="$p"
    fi
    echo "$port"
}

phase_validate() {
    header "Phase 3/4 — 环境验证"

    local port
    port=$(get_port)

    # --- 端口占用检查 ---
    local port_busy=false
    if command -v ss &>/dev/null; then
        if ss -tlnp 2>/dev/null | grep -q ":${port} "; then
            port_busy=true
        fi
    elif command -v netstat &>/dev/null; then
        if netstat -tlnp 2>/dev/null | grep -q ":${port} "; then
            port_busy=true
        fi
    fi
    if [[ "$port_busy" == true ]]; then
        warn "端口 ${port} 已被占用"
        warn "请修改 .env 中的 PORT，或释放端口: ss -tlnp | grep :${port}"
    else
        success "端口 ${port} 可用"
    fi

    # --- MariaDB 连通 (可选) ---
    if [[ -f "$ENV_FILE" ]]; then
        local db_host db_port db_user
        db_host=$(grep -oP '^\s*DB_HOST\s*=\s*"?\K[^"]+' "$ENV_FILE" 2>/dev/null) || true
        db_port=$(grep -oP '^\s*DB_PORT\s*=\s*\K\d+' "$ENV_FILE" 2>/dev/null) || true
        db_user=$(grep -oP '^\s*DB_USER\s*=\s*"?\K[^"]+' "$ENV_FILE" 2>/dev/null) || true
        db_port="${db_port:-3306}"

        if [[ -n "$db_host" && -n "$db_user" ]]; then
            if timeout 3 bash -c "echo >/dev/tcp/${db_host}/${db_port}" 2>/dev/null; then
                success "MariaDB (${db_host}:${db_port}) 网络可达"
            else
                warn "MariaDB (${db_host}:${db_port}) 不可达 — 皮肤站功能将不可用"
            fi
        else
            info "数据库未配置，跳过连通检查"
        fi
    fi

    # --- LLM API 连通 (可选) ---
    if [[ -f "$ENV_FILE" ]]; then
        local llm_url
        llm_url=$(grep -oP '^\s*LLAMA_SERVER_URL\s*=\s*"?\K[^"]+' "$ENV_FILE" 2>/dev/null) || true

        if [[ -n "$llm_url" && "$llm_url" != *"127.0.0.1:11434"* ]]; then
            if command -v curl &>/dev/null; then
                if curl -sf --connect-timeout 3 -o /dev/null "$llm_url" 2>/dev/null; then
                    success "LLM API 可达"
                else
                    warn "LLM API 不可达 — AI 聊天功能将不可用"
                fi
            else
                info "curl 未安装，跳过 LLM 连通检查"
            fi
        else
            info "LLM API 使用默认地址，跳过连通检查"
        fi
    fi
}

# ==============================================================================
#  Phase 4: 启动
# ==============================================================================
phase_start() {
    header "Phase 4/4 — 启动 Stupid_Bot"

    # 拦截未配置的 .env
    if [[ -f "$ENV_FILE" ]] && grep -qE 'YOUR_QQ_NUMBER' "$ENV_FILE" 2>/dev/null; then
        error ".env 中 SUPERUSERS 仍为占位符，请先编辑:"
        error "  nano $ENV_FILE"
        error "  然后运行: $0 --start-only"
        exit 4
    fi

    # 确保 venv 激活
    if [[ -z "${VIRTUAL_ENV:-}" ]]; then
        # shellcheck disable=SC1091
        source "$VENV_DIR/bin/activate"
    fi

    cd "$PROJECT_DIR"

    local port
    port=$(get_port)

    echo ""
    info "提醒: NapCat (QQ 协议端) 需独立运行"
    info "  如未启动 NapCat，机器人将无法收发 QQ 消息"
    if [[ -f "$HOME/napcat.sh" ]]; then
        info "  NapCat 脚本位于: ~/napcat.sh"
    fi
    echo ""
    info "正在启动 Stupid_Bot ..."
    info "  WebUI:  http://localhost:${port}/ui/"
    info "  按 Ctrl+C 停止"
    echo ""

    # exec 替换当前进程，信号直达 Python
    exec python "$BOT_PY"
}

# ==============================================================================
#  安装完成汇总
# ==============================================================================
print_summary() {
    header "安装完成 — 状态汇总"

    if [[ -z "${VIRTUAL_ENV:-}" && -f "$VENV_DIR/bin/activate" ]]; then
        # shellcheck disable=SC1091
        source "$VENV_DIR/bin/activate"
    fi

    local py_ver pkg_count port
    py_ver=$(python --version 2>&1) || py_ver="未知"
    pkg_count=$(python -m pip list --format=columns 2>/dev/null | tail -n +3 | wc -l) || pkg_count="?"
    port=$(get_port)

    echo -e "  Python:     ${GREEN}${py_ver}${NC}"
    echo -e "  虚拟环境:   ${GREEN}.venv${NC}"
    echo -e "  已安装包:   ${GREEN}${pkg_count} 个${NC}"
    echo -e "  配置文件:   ${GREEN}.env${NC}"
    echo -e "  端口:       ${CYAN}${port}${NC}"
    echo -e "  WebUI:      ${CYAN}http://localhost:${port}/ui/${NC}"
    echo ""

    if grep -qE 'YOUR_QQ_NUMBER' "$ENV_FILE" 2>/dev/null; then
        warn ".env 尚未配置完成，请编辑后再启动:"
        info "  nano $ENV_FILE"
        info "  然后: $0 --start-only"
    else
        info "启动命令: $0 --start-only"
        info "或手动:   cd $(basename "$PROJECT_DIR") && source .venv/bin/activate && python bot.py"
    fi
    echo ""
}

# ==============================================================================
#  主入口
# ==============================================================================
main() {
    echo ""
    echo -e "${BOLD}${CYAN}╔══════════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}${CYAN}║        Stupid_Bot 一键安装与启动脚本            ║${NC}"
    echo -e "${BOLD}${CYAN}║      NoneBot2 + FastAPI + OneBot V11            ║${NC}"
    echo -e "${BOLD}${CYAN}╚══════════════════════════════════════════════════╝${NC}"
    echo ""

    cd "$PROJECT_DIR"

    case "$MODE" in
        install)
            phase_check
            phase_deps
            phase_config
            phase_validate
            print_summary
            ;;
        start)
            if [[ ! -d "$VENV_DIR" ]]; then
                error "虚拟环境不存在，请先运行: $0 --install-only"
                exit 1
            fi
            if [[ ! -f "$ENV_FILE" ]]; then
                error ".env 不存在，请先运行: $0 --install-only"
                exit 1
            fi
            phase_start
            ;;
        full)
            phase_check
            phase_deps
            phase_config
            phase_validate
            print_summary
            phase_start
            ;;
    esac
}

main
