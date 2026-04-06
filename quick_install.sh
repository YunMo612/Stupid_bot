#!/usr/bin/env bash
# ==============================================================================
# Stupid_bot 终极自动化部署脚本 (带滚屏进度条 + Docker自选 + 动态裁剪 + 皮肤站 + 自动清理)
# ==============================================================================
set -e

# --- 1. 界面模式选择 ---
echo -e "\033[1;36m=================================================\033[0m"
echo -e "\033[1;36m      Stupid_bot 自动安装与环境部署脚本          \033[0m"
echo -e "\033[1;36m=================================================\033[0m"
echo "请选择安装界面模式 (Select UI Mode):"
echo "1) TUI 模式 (图形化文本界面，推荐)"
echo "2) CLI 模式 (纯命令行交互)"
read -p "请输入 [1/2] (默认1): " UI_CHOICE

USE_TUI=true
if [ "$UI_CHOICE" == "2" ]; then USE_TUI=false; fi

if $USE_TUI; then
    if ! command -v whiptail &> /dev/null; then
        echo "未检测到 whiptail，正在为您自动安装..."
        sudo apt-get update -y && sudo apt-get install -y whiptail
    fi
fi

# --- 2. 封装交互与进度条函数 ---
show_msg() {
    local title=$1; local msg=$2
    if $USE_TUI; then
        whiptail --title "$title" --msgbox "$msg" 15 60
    else
        echo -e "\n\033[1;32m[$title]\033[0m\n$msg\n按回车键继续..."
        read -r
    fi
}

get_input() {
    local title=$1; local msg=$2; local default=$3; local RESULT
    if $USE_TUI; then
        RESULT=$(whiptail --title "$title" --inputbox "$msg" 10 60 "$default" 3>&1 1>&2 2>&3)
    else
        read -p "[$title] $msg [$default]: " RESULT
        if [ -z "$RESULT" ]; then RESULT=$default; fi
    fi
    echo "$RESULT"
}

ask_yes_no() {
    local title=$1; local msg=$2
    if $USE_TUI; then
        whiptail --title "$title" --yesno "$msg" 10 60 && return 0 || return 1
    else
        read -p "[$title] $msg (y/n) [y]: " ans
        if [[ "$ans" == "n" || "$ans" == "N" ]]; then return 1; else return 0; fi
    fi
}

# 🌟 将总步数增加为 9 步 (加入了自动清理步骤)
TOTAL_STEPS=9
CURRENT_STEP=0

advance_step() {
    ((CURRENT_STEP++))
    local step_name="$1"
    local pct=$(( CURRENT_STEP * 100 / TOTAL_STEPS ))
    local width=40
    local filled=$(( pct * width / 100 ))
    local empty=$(( width - filled ))
    local bar=$(printf "%${filled}s" | tr ' ' '█')
    local space=$(printf "%${empty}s" | tr ' ' '░')
    
    echo -e "\n\033[1;34m=================================================\033[0m"
    echo -e "\033[1;32m总体进度: [${bar}${space}] ${pct}% ($CURRENT_STEP/$TOTAL_STEPS)\033[0m"
    echo -e "\033[1;36m▶ 当前任务: $step_name\033[0m"
    echo -e "\033[1;34m=================================================\033[0m"
}

run_logged() {
    "$@" 2>&1 | while IFS= read -r line; do
        echo -e "\033[1;30m│\033[0m $line"
    done
}

# --- 3. 获取用户信息与 QQ 号 ---
CURRENT_USER=${SUDO_USER:-$USER}
TARGET_USER=$(get_input "用户配置" "请输入将要运行Bot的系统用户名 (UserName):" "$CURRENT_USER")
USER_HOME="/home/$TARGET_USER"

if [ -z "$TARGET_USER" ]; then echo "用户名不能为空，退出。"; exit 1; fi
sudo mkdir -p "$USER_HOME"

BOT_QQ=$(get_input "机器人配置" "请输入您准备作为机器人的 QQ 号码:\n(这将在稍后用于配置 NapCat 与环境文件)" "123456789")

# --- 4. 基础环境安装 ---
advance_step "安装基础环境依赖 (apt-get)"
run_logged sudo apt-get update -y
run_logged sudo apt-get install -y git curl unzip python3 python3-pip python3-venv pipx mariadb-server

# --- 5. NapCat 安装与 QQ 配置 ---
INSTALL_NAPCAT=false
USE_DOCKER_NAPCAT=false
DOCKER_FLAG=""

if ask_yes_no "NapCat 安装" "是否需要在此服务器上安装 NapCat (QQ 协议端)？"; then
    INSTALL_NAPCAT=true
    if ask_yes_no "NapCat 安装方式" "您是否希望使用 Docker 容器化安装 NapCat？\n\n[Yes] : 使用 Docker 安装 (强烈推荐，环境隔离更稳定)\n[No]  : 使用原生脚本安装 (适合无 Docker 环境)"; then
        USE_DOCKER_NAPCAT=true
        DOCKER_FLAG="--docker y"
    fi
    advance_step "部署 NapCat ($([ "$USE_DOCKER_NAPCAT" = true ] && echo "Docker版" || echo "原生版"))"
    run_logged curl -o napcat.sh https://nclatest.znin.net/NapNeko/NapCat-Installer/main/script/install.sh
    run_logged sudo bash napcat.sh $DOCKER_FLAG --qq "$BOT_QQ" --mode ws --proxy 0 --confirm || echo -e "\033[1;33mNapCat 部署遇到交互，请稍后手动检查。\033[0m"
else
    advance_step "跳过 NapCat 协议端安装"
    echo -e "\033[1;30m│\033[0m 用户选择跳过。"
fi

# --- 6. 分支与插件动态选择 ---
if $USE_TUI; then
    BRANCH_CHOICE=$(whiptail --title "选择拉取分支" --menu "请选择您要部署的版本:" 15 65 2 \
    "main" "稳定版 (推荐，运行稳定但更新较慢)" "dev" "开发版 (体验新功能但可能不稳定)" 3>&1 1>&2 2>&3)
    [ -z "$BRANCH_CHOICE" ] && BRANCH_CHOICE="main"
else
    echo -e "\n\033[1;32m[版本选择]\033[0m"
    echo "1) main - 稳定版 (推荐)  |  2) dev - 开发版"
    read -p "请输入 [1/2] (默认1): " branch_ans
    [ "$branch_ans" == "2" ] && BRANCH_CHOICE="dev" || BRANCH_CHOICE="main"
fi

advance_step "获取云端插件列表 ($BRANCH_CHOICE)"
run_logged curl -s -o /tmp/plugins.json "https://raw.githubusercontent.com/YunMo612/Stupid_bot/${BRANCH_CHOICE}/plugins.json"

cat << 'EOF' > /tmp/parse_plugins.py
import json, sys
try:
    with open('/tmp/plugins.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
except Exception:
    sys.exit(1)

mandatories = []
options_tui = []
options_cli = []

if isinstance(data, dict):
    for k, v in data.items():
        if not v.get('can_delete', True):
            mandatories.append(k)
        else:
            name_zh = v.get('name_zh', k)
            options_tui.extend([k, name_zh.replace(' ', '_'), "ON"])
            options_cli.append(f"{k}:{name_zh}")

with open('/tmp/mandatories.txt', 'w', encoding='utf-8') as f: f.write(",".join(mandatories))
with open('/tmp/options_tui.txt', 'w', encoding='utf-8') as f: f.write(" ".join(f'"{x}"' for x in options_tui))
with open('/tmp/options_cli.txt', 'w', encoding='utf-8') as f: f.write("\n".join(options_cli))
EOF

PRUNE_PLUGINS=false
NEEDS_BS_PROMPT=false

if python3 /tmp/parse_plugins.py; then
    PRUNE_PLUGINS=true
    MANDATORY_PLUGINS=$(cat /tmp/mandatories.txt)
    TUI_OPTS_CONTENT=$(cat /tmp/options_tui.txt)
    SELECTED_PLUGINS=""
    
    if [ -n "$TUI_OPTS_CONTENT" ]; then
        if $USE_TUI; then
            eval "CHOICES=($TUI_OPTS_CONTENT)"
            if [ ${#CHOICES[@]} -gt 0 ]; then
                SELECTED=$(whiptail --title "插件定制" --checklist "底层必选插件已被系统强制保留。\n请选择您要启用的可选扩展插件 (空格切换，回车确认):" 20 65 10 "${CHOICES[@]}" 3>&1 1>&2 2>&3)
                SELECTED_PLUGINS=$(echo "$SELECTED" | tr -d '"')
            fi
        else
            echo -e "\n底层必选插件已被强制保留。以下为可选扩展插件:"
            IFS=$'\n' read -d '' -r -a cli_opts < /tmp/options_cli.txt || true
            idx=1; declare -A CLI_MAP
            for opt in "${cli_opts[@]}"; do
                k=$(echo "$opt" | cut -d':' -f1); name=$(echo "$opt" | cut -d':' -f2)
                echo "$idx) $k ($name)"; CLI_MAP[$idx]=$k; ((idx++))
            done
            read -p "请输入要安装的插件序号 (用空格分隔，直接回车表示全部安装): " keep_input
            if [ -z "$keep_input" ]; then
                SELECTED_PLUGINS="${CLI_MAP[@]}"
            else
                for i in $keep_input; do [ -n "${CLI_MAP[$i]}" ] && SELECTED_PLUGINS="$SELECTED_PLUGINS ${CLI_MAP[$i]}"; done
            fi
        fi
    fi
    
    if [[ "$SELECTED_PLUGINS" == *"server_tools"* ]] || [[ "$SELECTED_PLUGINS" == *"all"* ]] || [ -z "$SELECTED_PLUGINS" ] && [ -n "${cli_opts[*]}" ]; then
        NEEDS_BS_PROMPT=true
    fi
fi

# --- 7. 拉取项目与动态裁剪 ---
advance_step "拉取代码库并动态裁剪"
cd "$USER_HOME"
if [ ! -d "Stupid_bot" ]; then
    run_logged sudo git clone -b "$BRANCH_CHOICE" https://github.com/YunMo612/Stupid_bot.git
fi

if [ "$PRUNE_PLUGINS" = true ]; then
    cat << 'EOF' > /tmp/clean_plugins.py
import json, sys, os, shutil
selected = sys.argv[1].split() if len(sys.argv) > 1 else []
mandatory = sys.argv[2].split(',') if len(sys.argv) > 2 and sys.argv[2] else []
keep_list = set(selected + mandatory)
project_dir = sys.argv[3]
plugins_json_path = os.path.join(project_dir, 'plugins.json')
plugins_dir = os.path.join(project_dir, 'src', 'plugins')

if os.path.exists(plugins_json_path):
    try:
        with open(plugins_json_path, 'r', encoding='utf-8') as f: data = json.load(f)
        new_data = {k: v for k, v in data.items() if k in keep_list}
        with open(plugins_json_path, 'w', encoding='utf-8') as f: json.dump(new_data, f, ensure_ascii=False, indent=4)
    except Exception: pass

if os.path.exists(plugins_dir):
    for item in os.listdir(plugins_dir):
        item_path = os.path.join(plugins_dir, item)
        if os.path.isdir(item_path) and not item.startswith('__') and item not in keep_list:
            shutil.rmtree(item_path)
EOF
    run_logged sudo python3 /tmp/clean_plugins.py "$SELECTED_PLUGINS" "$MANDATORY_PLUGINS" "$USER_HOME/Stupid_bot"
fi

# --- 8. 配置虚拟环境 ---
advance_step "配置 Python 虚拟环境与依赖"
cd "$USER_HOME/Stupid_bot"
run_logged sudo python3 -m venv venv
run_logged sudo ./venv/bin/pip install -r requirements.txt
run_logged sudo ./venv/bin/pip install python-multipart
run_logged sudo chown -R "$TARGET_USER:$TARGET_USER" "$USER_HOME"
run_logged sudo -u "$TARGET_USER" pipx ensurepath
run_logged sudo -u "$TARGET_USER" pipx install nb-cli

# --- 9. MariaDB 自动化配置 ---
if $USE_TUI; then
    DB_USER=$(whiptail --title "数据库配置" --inputbox "请输入要创建的 MariaDB 用户名:" 10 60 "yunmo" 3>&1 1>&2 2>&3)
    while true; do
        DB_PASS=$(whiptail --title "数据库配置" --passwordbox "请输入该用户的密码:" 10 60 3>&1 1>&2 2>&3)
        DB_PASS2=$(whiptail --title "数据库配置" --passwordbox "请再次输入密码以确认:" 10 60 3>&1 1>&2 2>&3)
        if [ "$DB_PASS" == "$DB_PASS2" ] && [ -n "$DB_PASS" ]; then break; else whiptail --title "错误" --msgbox "密码不一致或为空，重试！" 8 45; fi
    done
else
    read -p "[数据库配置] 请输入要创建的 MariaDB 用户名 [yunmo]: " DB_USER
    DB_USER=${DB_USER:-yunmo}
    while true; do
        read -s -p "[数据库配置] 请输入密码: " DB_PASS; echo ""
        read -s -p "[数据库配置] 再次输入: " DB_PASS2; echo ""
        if [ "$DB_PASS" == "$DB_PASS2" ] && [ -n "$DB_PASS" ]; then break; else echo -e "\033[1;31m密码不一致或为空，重试！\033[0m"; fi
    done
fi

advance_step "自动配置 MariaDB 与安全加固"
run_logged sudo systemctl start mariadb
run_logged sudo systemctl enable mariadb
run_logged sudo mariadb -e "DELETE FROM mysql.global_priv WHERE User='';"
run_logged sudo mariadb -e "DELETE FROM mysql.global_priv WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');"
run_logged sudo mariadb -e "DROP DATABASE IF EXISTS test;"
run_logged sudo mariadb -e "DELETE FROM mysql.db WHERE Db='test' OR Db='test\\_%';"
run_logged sudo mariadb -e "CREATE DATABASE IF NOT EXISTS blessing_skin CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
run_logged sudo mariadb -e "CREATE DATABASE IF NOT EXISTS stupid_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
run_logged sudo mariadb -e "CREATE USER IF NOT EXISTS '${DB_USER}'@'%' IDENTIFIED BY '${DB_PASS}';"
run_logged sudo mariadb -e "GRANT ALL PRIVILEGES ON blessing_skin.* TO '${DB_USER}'@'%';"
run_logged sudo mariadb -e "GRANT ALL PRIVILEGES ON stupid_db.* TO '${DB_USER}'@'%';"
run_logged sudo mariadb -e "GRANT SUPER ON *.* TO '${DB_USER}'@'%';"
run_logged sudo mariadb -e "SET GLOBAL event_scheduler = ON;"
run_logged sudo mariadb -e "FLUSH PRIVILEGES;"

# --- 10. 数据库导入与迁移 ---
advance_step "初始化或迁移数据库"
if ask_yes_no "数据迁移" "您是否有旧的数据库备份文件 (stupid_db.sql) 需要迁移？\n\n选 [Yes]: 暂停等待您上传备份文件。\n选 [No] : 自动导入自带的基础结构。"; then
    import_sql() {
        if $USE_TUI; then
            while true; do
                if [ -f "$USER_HOME/stupid_db.sql" ] || [ -f "$USER_HOME/Stupid_bot.sql" ]; then
                    SQL_FILE="$USER_HOME/stupid_db.sql"; [ -f "$USER_HOME/Stupid_bot.sql" ] && SQL_FILE="$USER_HOME/Stupid_bot.sql"
                    run_logged sudo mariadb stupid_db < "$SQL_FILE"
                    run_logged sudo mv "$SQL_FILE" "$USER_HOME/stupid_db_backup.sql"
                    whiptail --title "导入成功" --msgbox "旧数据库导入自动完成！\n已重命名为 stupid_db_backup.sql" 8 55; break
                else
                    if whiptail --title "等待上传" --yes-button "已上传" --no-button "跳过" --yesno "请将 sql 备份上传至目录:\n$USER_HOME\n确认上传完毕请点击继续。" 10 60; then continue; else break; fi
                fi
            done
        else
            while true; do
                if [ -f "$USER_HOME/stupid_db.sql" ] || [ -f "$USER_HOME/Stupid_bot.sql" ]; then
                    SQL_FILE="$USER_HOME/stupid_db.sql"; [ -f "$USER_HOME/Stupid_bot.sql" ] && SQL_FILE="$USER_HOME/Stupid_bot.sql"
                    run_logged sudo mariadb stupid_db < "$SQL_FILE"
                    run_logged sudo mv "$SQL_FILE" "$USER_HOME/stupid_db_backup.sql"
                    echo "数据库迁移成功！"; break
                else
                    read -p "请上传 sql 备份至 $USER_HOME 目录，上传完按回车 (输入 skip 跳过): " ans
                    [ "$ans" == "skip" ] && break
                fi
            done
        fi
    }
    import_sql
else
    DEFAULT_SQL="$USER_HOME/Stupid_bot/stupid_db.sql"
    if [ -f "$DEFAULT_SQL" ]; then
        run_logged sudo mariadb stupid_db < "$DEFAULT_SQL"
        echo -e "\033[1;30m│\033[0m 基础数据表结构已成功导入！"
    fi
fi

# --- 11. Blessing Skin 自动化部署 ---
BS_MSG=""
if [ "$NEEDS_BS_PROMPT" = true ]; then
    advance_step "部署 Blessing Skin 皮肤站"
    if ask_yes_no "附加部署" "检测到您勾选了 MC 服务器相关插件 (server_tools)。\n\n是否需要在此服务器上一键启动 Blessing Skin (皮肤站) 容器，并自动连入配置好的数据库？"; then
        BS_PORT=$(get_input "皮肤站配置" "请输入 Blessing Skin Web页面绑定的端口号 (例如: 8000):" "8000")
        
        show_msg "拉取容器" "正在为您拉取官方 Blessing Skin 镜像并配置数据库挂载，请稍候..."
        
        if ! command -v docker &> /dev/null; then
            echo -e "\033[1;33m│ 未检测到 Docker，正在自动安装...\033[0m"
            run_logged curl -fsSL https://get.docker.com | sudo bash -s docker
        fi
        
        sudo mkdir -p "$USER_HOME/blessing_skin_data"
        sudo chown -R 33:33 "$USER_HOME/blessing_skin_data" 
        
        run_logged sudo docker run -d --name blessing-skin --restart=always \
          -p ${BS_PORT}:80 \
          --add-host host.docker.internal:host-gateway \
          -e DB_CONNECTION=mysql \
          -e DB_HOST=host.docker.internal \
          -e DB_PORT=3306 \
          -e DB_DATABASE=blessing_skin \
          -e DB_USERNAME="${DB_USER}" \
          -e DB_PASSWORD="${DB_PASS}" \
          -v "$USER_HOME/blessing_skin_data:/app/storage" \
          printempw/blessing-skin-server:latest || echo -e "\033[1;31m│ 皮肤站启动失败，请检查端口是否被占用。\033[0m"
          
        BS_MSG="- 皮肤站后台: [ http://服务器IP:${BS_PORT} ] (初始配置请访问此地址)"
    else
        echo -e "\033[1;30m│\033[0m 用户选择跳过 Blessing Skin 部署。"
    fi
else
    advance_step "跳过附加部署"
    echo -e "\033[1;30m│\033[0m 未检测到依赖皮肤站的插件，已跳过此步骤。"
fi

# --- 12. 清理临时文件 (新增) ---
advance_step "清理安装产生的临时文件"
run_logged rm -f /tmp/plugins.json /tmp/parse_plugins.py /tmp/mandatories.txt /tmp/options_tui.txt /tmp/options_cli.txt /tmp/clean_plugins.py
# 如果下载了 napcat.sh 脚本，顺手也清理掉
if [ -f "napcat.sh" ]; then
    run_logged rm -f napcat.sh
fi
echo -e "\033[1;30m│\033[0m 所有解析脚本与缓存已清空，保持系统整洁！"

# --- 13. 终极提示与唤起 NapCat 扫码 ---
FINAL_MSG="✅ 安装全部完成！

您的机器人环境已就绪。
- 机器人 QQ: [ ${BOT_QQ} ]
- 数据库账户: [ ${DB_USER} ]
${BS_MSG}

【⚠️ 启动前配置】：
请务必修改 .env 配置文件，填入您的超级管理员 QQ 以及数据库账号密码！
命令: nano $USER_HOME/Stupid_bot/.env
    （或者使用您喜欢的文本编辑器）

【启动机器人主控】：
cd $USER_HOME/Stupid_bot
source venv/bin/activate
nb run --reload"

show_msg "部署完毕" "$FINAL_MSG"

if [ "$INSTALL_NAPCAT" = true ]; then
    echo -e "\n\033[1;36m=================================================\033[0m"
    echo -e "\033[1;33m即将进入 NapCat 容器为您显示登录二维码！\033[0m"
    echo -e "\033[1;36m请掏出手机准备扫码登录。\033[0m"
    echo -e "*(如果二维码未完全加载，可按 \033[1;31mCtrl+C\033[0m 退出，之后手动执行 'sudo docker logs -f napcat' 再次查看)*"
    echo -e ""
    echo -e "\033[1;31m【⚠️ 扫码常见问题：提示“登录超时”怎么办？】\033[0m"
    echo -e "如果手机 QQ 扫码后一直转圈，最后提示 \033[1;33m“登录超时”\033[0m 或 \033[1;33m“网络异常”\033[0m，请按以下步骤解决："
    echo -e "  1. 在当前黑框按 \033[1;31mCtrl+C\033[0m 退出二维码界面"
    if [ "$USE_DOCKER_NAPCAT" = true ]; then
        echo -e "  2. 输入命令重启协议端：\033[1;32msudo docker restart napcat\033[0m"
        echo -e "  3. 再次获取全新二维码：\033[1;32msudo docker logs -f napcat\033[0m"
    else
        echo -e "  2. 请重新运行 NapCat 原生启动命令或重启服务。"
    fi
    echo -e "  \033[1;35m*💡 玄学技巧：扫码时将手机 WiFi 关闭，使用 4G/5G 流量扫码，能大幅降低超时概率！\033[0m"
    echo -e "\033[1;36m=================================================\033[0m"
    sleep 6 
    
    if [ "$USE_DOCKER_NAPCAT" = true ]; then
        sudo docker logs -f napcat
    fi
else
    echo -e "\n🎉 Stupid_bot 自动化部署执行完毕！\n"
fi