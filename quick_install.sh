#!/usr/bin/env bash
# ==============================================================================
# Stupid_bot 终极自动化部署脚本 (动态裁剪插件 + 数据库全自动配置)
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

# --- 2. 封装交互函数 ---
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

# --- 3. 获取用户信息 ---
CURRENT_USER=${SUDO_USER:-$USER}
TARGET_USER=$(get_input "用户配置" "请输入将要运行Bot的系统用户名 (UserName):" "$CURRENT_USER")
USER_HOME="/home/$TARGET_USER"

if [ -z "$TARGET_USER" ]; then echo "用户名不能为空，退出。"; exit 1; fi
sudo mkdir -p "$USER_HOME"

# --- 4. 基础环境安装 ---
show_msg "环境安装" "步骤 1/7: 正在更新 apt 并安装基础依赖...\n(git, curl, python3, venv, mariadb-server 等)"
sudo apt-get update -y
sudo apt-get install -y git curl unzip python3 python3-pip python3-venv pipx mariadb-server

# --- 5. NapCat 安装 ---
if ask_yes_no "NapCat 安装" "步骤 2/7: 是否需要在此服务器上安装 NapCat (QQ 协议端)？"; then
    show_msg "NapCat 安装" "正在调用 NapCat 官方安装脚本..."
    curl -o napcat.sh https://nchat.qidianem.com/cmds/script.sh && sudo bash napcat.sh || echo "可能需手动确认。"
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

show_msg "插件获取" "步骤 3/7: 正在从云端获取可选插件列表，请稍候..."
curl -s -o /tmp/plugins.json "https://raw.githubusercontent.com/YunMo612/Stupid_bot/${BRANCH_CHOICE}/plugins.json"

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
else
    show_msg "网络提示" "未能成功从 GitHub 获取插件配置，将为您默认安装所有插件。"
fi

# --- 7. 拉取项目与动态裁剪 ---
show_msg "拉取与裁剪" "步骤 4/7: 正在克隆 [$BRANCH_CHOICE] 分支，并裁剪未选择的插件..."
cd "$USER_HOME"
if [ ! -d "Stupid_bot" ]; then
    sudo git clone -b "$BRANCH_CHOICE" https://github.com/YunMo612/Stupid_bot.git
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
    sudo python3 /tmp/clean_plugins.py "$SELECTED_PLUGINS" "$MANDATORY_PLUGINS" "$USER_HOME/Stupid_bot"
fi

# --- 8. 配置虚拟环境 ---
show_msg "配置虚拟环境" "步骤 5/7: 正在配置 Python 虚拟环境与依赖..."
cd "$USER_HOME/Stupid_bot"
sudo python3 -m venv venv
sudo ./venv/bin/pip install -r requirements.txt
sudo ./venv/bin/pip install python-multipart
sudo chown -R "$TARGET_USER:$TARGET_USER" "$USER_HOME"
sudo -u "$TARGET_USER" pipx ensurepath
sudo -u "$TARGET_USER" pipx install nb-cli

# --- 9. MariaDB 自动化配置 ---
show_msg "配置数据库" "步骤 6/7: 接下来将配置 MariaDB 账户与安全加固。"
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

sudo systemctl start mariadb || true
sudo systemctl enable mariadb || true
sudo mariadb -e "DELETE FROM mysql.global_priv WHERE User='';"
sudo mariadb -e "DELETE FROM mysql.global_priv WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');"
sudo mariadb -e "DROP DATABASE IF EXISTS test;"
sudo mariadb -e "DELETE FROM mysql.db WHERE Db='test' OR Db='test\\_%';"
sudo mariadb -e "CREATE DATABASE IF NOT EXISTS blessing_skin CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
sudo mariadb -e "CREATE DATABASE IF NOT EXISTS stupid_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
sudo mariadb -e "CREATE USER IF NOT EXISTS '${DB_USER}'@'%' IDENTIFIED BY '${DB_PASS}';"
sudo mariadb -e "GRANT ALL PRIVILEGES ON blessing_skin.* TO '${DB_USER}'@'%';"
sudo mariadb -e "GRANT ALL PRIVILEGES ON stupid_db.* TO '${DB_USER}'@'%';"
sudo mariadb -e "GRANT SUPER ON *.* TO '${DB_USER}'@'%';"
sudo mariadb -e "SET GLOBAL event_scheduler = ON;"
sudo mariadb -e "FLUSH PRIVILEGES;"

# --- 10. 数据库导入与迁移 ---
if ask_yes_no "数据迁移" "步骤 7/7: 您是否有旧的数据库备份文件 (stupid_db.sql) 需要迁移？\n\n选 [Yes]: 暂停等待您上传备份文件。\n选 [No] : 自动导入自带的基础结构。"; then
    import_sql() {
        if $USE_TUI; then
            while true; do
                if [ -f "$USER_HOME/stupid_db.sql" ] || [ -f "$USER_HOME/Stupid_bot.sql" ]; then
                    SQL_FILE="$USER_HOME/stupid_db.sql"; [ -f "$USER_HOME/Stupid_bot.sql" ] && SQL_FILE="$USER_HOME/Stupid_bot.sql"
                    sudo mariadb stupid_db < "$SQL_FILE"
                    sudo mv "$SQL_FILE" "$USER_HOME/stupid_db_backup.sql"
                    whiptail --title "导入成功" --msgbox "旧数据库导入自动完成！\n已重命名为 stupid_db_backup.sql" 8 55; break
                else
                    if whiptail --title "等待上传" --yes-button "已上传" --no-button "跳过" --yesno "请将 sql 备份上传至目录:\n$USER_HOME\n确认上传完毕请点击继续。" 10 60; then continue; else break; fi
                fi
            done
        else
            while true; do
                if [ -f "$USER_HOME/stupid_db.sql" ] || [ -f "$USER_HOME/Stupid_bot.sql" ]; then
                    SQL_FILE="$USER_HOME/stupid_db.sql"; [ -f "$USER_HOME/Stupid_bot.sql" ] && SQL_FILE="$USER_HOME/Stupid_bot.sql"
                    sudo mariadb stupid_db < "$SQL_FILE"
                    sudo mv "$SQL_FILE" "$USER_HOME/stupid_db_backup.sql"
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
    show_msg "初始化数据库" "自动导入自带基础结构 (stupid_db.sql)..."
    DEFAULT_SQL="$USER_HOME/Stupid_bot/stupid_db.sql"
    if [ -f "$DEFAULT_SQL" ]; then
        sudo mariadb stupid_db < "$DEFAULT_SQL"
        show_msg "导入成功" "基础数据表创建完毕！"
    fi
fi

# --- 11. 终极提示 ---
FINAL_MSG="✅ 安装全部完成！

数据库账户已设定为: [ ${DB_USER} ]

【⚠️ 启动前配置】：
请修改 .env 配置文件，填入数据库账号密码！
命令: nano $USER_HOME/Stupid_bot/.env

【启动机器人】：
cd $USER_HOME/Stupid_bot
source venv/bin/activate
python bot.py"

show_msg "部署完毕" "$FINAL_MSG"
echo -e "\n🎉 Stupid_bot 自动化部署执行完毕！\n"