#!/bin/bash
# healthcheck_agelytics.sh — Verifica se overlay e watcher estão rodando, reinicia se necessário

REPO="/home/linuxadmin/repos/agelytics"
LOG="/tmp/agelytics_healthcheck.log"

check_and_restart() {
    local name=$1
    local pattern=$2
    local script=$3
    
    if ! pgrep -f "$pattern" > /dev/null; then
        echo "$(date): $name caiu, reiniciando..." >> "$LOG"
        cd "$REPO" && nohup bash "$script" > /tmp/${name}.log 2>&1 &
        sleep 2
        if pgrep -f "$pattern" > /dev/null; then
            echo "$(date): $name reiniciado com sucesso" >> "$LOG"
        else
            echo "$(date): FALHA ao reiniciar $name" >> "$LOG"
        fi
    fi
}

# Verifica overlay
check_and_restart "overlay" "uvicorn.*5555" "scripts/start_overlay.sh"

# Verifica watcher
check_and_restart "watcher" "game_watcher" "scripts/start_watcher.sh"
