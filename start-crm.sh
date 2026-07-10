#!/usr/bin/env bash
set -euo pipefail

###############################################################################
# start-crm.sh — One command to start everything for CRM development
#
# What it does:
#   1. Checks if tmux session "crm" exists; if yes, attaches to it
#   2. If not, creates it with 3 windows:
#      - Window 0 (dev):         npm run dev on port 8085
#      - Window 1 (localtunnel): localtunnel with subdomain
#      - Window 2 (localhost_run): localhost.run SSH tunnel
#   3. Waits for localtunnel to produce a URL
#   4. Updates site_config.json host_name with the new URL
#   5. Registers the Vobiz webhook with the new URL
#   6. Attaches to the tmux session
###############################################################################

PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
FRONTEND_DIR="$PROJECT_DIR/frontend"
SESSION="crm"
VOBIZ_APP_ID="12995932524652812"
DOCKER_CONTAINER="crm-frappe-1"
SITE="crm.localhost"

# Preferred subdomain (localtunnel may ignore if taken)
LT_SUBDOMAIN="tender-planes-wait"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m' # No Color

log()  { echo -e "${GREEN}[✓]${NC} $*"; }
warn() { echo -e "${YELLOW}[!]${NC} $*"; }
info() { echo -e "${CYAN}[i]${NC} $*"; }
err()  { echo -e "${RED}[✗]${NC} $*"; }

setup_mongodb_proxy() {
    info "Setting up MongoDB WSL proxy..."
    # 1. Detect WSL IP
    local wsl_ip=""
    wsl_ip=$(ip route show | grep default | awk '{print $3}' || true)
    if [ -n "$wsl_ip" ]; then
        echo "$wsl_ip" > "$PROJECT_DIR/scratch/wsl_ip.txt"
        log "Saved WSL gateway IP ($wsl_ip) to scratch/wsl_ip.txt"
    else
        warn "Could not detect WSL gateway IP!"
    fi

    # 2. Start Windows proxy if not already running on port 27018
    local ps_path="/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe"
    if [ -f "$ps_path" ]; then
        local conn_status=0
        "$ps_path" -Command "if (Get-NetTCPConnection -LocalPort 27018 -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }" 2>/dev/null && conn_status=1 || conn_status=0
        
        if [ "$conn_status" -eq 1 ]; then
            log "MongoDB proxy is already running on Windows port 27018"
        else
            info "Starting MongoDB proxy on Windows..."
            local win_proj_dir
            win_proj_dir=$(wslpath -w "$PROJECT_DIR" | tr -d '\r\n')
            "$ps_path" -Command "Start-Process python -ArgumentList '$win_proj_dir\\scratch\\mongo_proxy.py' -WindowStyle Hidden -WorkingDirectory '$win_proj_dir'"
            log "Started MongoDB proxy on Windows"
        fi
    else
        warn "Windows PowerShell not found at $ps_path, skipping proxy startup"
    fi
}

setup_mongodb_proxy

###############################################################################
# If session already exists, just attach
###############################################################################
if tmux has-session -t "$SESSION" 2>/dev/null; then
    log "tmux session '$SESSION' already running."

    # Check if services are alive
    DEV_RUNNING=$(tmux capture-pane -J -t "$SESSION:0" -p | grep -c "localhost:8085" || true)
    LT_RUNNING=$(tmux capture-pane -J -t "$SESSION:1" -p | grep -c "loca.lt" || true)
    LHR_RUNNING=$(tmux capture-pane -J -t "$SESSION:2" -p -S -200 | grep -c "lhr.life" || true)

    if [ "$DEV_RUNNING" -gt 0 ]; then
        log "Dev server is running"
    else
        warn "Dev server may have stopped — check window 0"
    fi

    TUNNEL_URL=""
    if [ "$LHR_RUNNING" -gt 0 ]; then
        TUNNEL_URL=$(tmux capture-pane -J -t "$SESSION:2" -p -S -200 | grep -oP 'https://[a-z0-9-]+\.lhr\.life' | tail -1 || true)
        if [ -n "$TUNNEL_URL" ]; then
            log "localhost.run: $TUNNEL_URL"
        fi
    fi

    if [ -z "$TUNNEL_URL" ] && [ "$LT_RUNNING" -gt 0 ]; then
        TUNNEL_URL=$(tmux capture-pane -J -t "$SESSION:1" -p -S - | grep -oP 'https://[a-z0-9-]+\.loca\.lt' | tail -1 || true)
        if [ -n "$TUNNEL_URL" ]; then
            log "Localtunnel: $TUNNEL_URL"
        fi
    fi

    if [ -n "$TUNNEL_URL" ]; then
        info "Updating site_config.json host_name → $TUNNEL_URL"
        docker exec "$DOCKER_CONTAINER" bash -c \
            "cd /home/frappe/frappe-bench && bench --site $SITE set-config host_name '$TUNNEL_URL'" \
            2>/dev/null && log "site_config updated" || warn "Failed to update site_config"

        info "Registering Vobiz webhook..."
        RESULT=$(docker exec -w /home/frappe/frappe-bench/sites "$DOCKER_CONTAINER" \
            /home/frappe/frappe-bench/env/bin/python -c \
            "import sys; sys.path.extend(['/home/frappe/frappe-bench/apps/frappe', '/home/frappe/frappe-bench/apps/crm']); import frappe; frappe.init(site='$SITE', sites_path='.'); frappe.connect(); s = frappe.get_single('CRM Vobiz Settings'); s.webhook_url_override = '$TUNNEL_URL'; s.save(); frappe.db.commit(); print(s.register_webhook('$VOBIZ_APP_ID')); frappe.db.commit()" \
            2>&1) || true

        if echo "$RESULT" | grep -qi "success\|registered\|webhook_url"; then
            log "Vobiz webhook registered successfully!"
        else
            warn "Webhook registration output: $RESULT"
        fi
    else
        warn "No active tunnel URL (localhost.run or localtunnel) found"
    fi

    info "Attaching to session..."
    tmux attach -t "$SESSION"
    exit 0
fi

###############################################################################
# Create new tmux session
###############################################################################
info "Creating tmux session '$SESSION'..."

# Window 0: Dev server
tmux new-session -d -s "$SESSION" -n dev -c "$FRONTEND_DIR"
tmux send-keys -t "$SESSION:dev" "npm run dev -- --host" Enter
log "Started dev server (window 0)"

# Window 1: Localtunnel
tmux new-window -t "$SESSION" -n localtunnel -c "$PROJECT_DIR"
tmux send-keys -t "$SESSION:localtunnel" \
    "npx -y localtunnel --port 8085 --subdomain $LT_SUBDOMAIN" Enter
log "Started localtunnel (window 1)"

# Window 2: localhost.run
tmux new-window -t "$SESSION" -n localhost_run -c "$PROJECT_DIR"
tmux send-keys -t "$SESSION:localhost_run" \
    "ssh -o StrictHostKeyChecking=no -R 80:localhost:8085 nokey@localhost.run" Enter
log "Started localhost.run (window 2)"

###############################################################################
# Wait for tunnel URL
###############################################################################
info "Waiting for tunnel URL..."
TUNNEL_URL=""
MAX_WAIT=60
WAITED=0

while [ -z "$TUNNEL_URL" ] && [ "$WAITED" -lt "$MAX_WAIT" ]; do
    sleep 3
    WAITED=$((WAITED + 3))
    # Try localhost.run first
    TUNNEL_URL=$(tmux capture-pane -J -t "$SESSION:localhost_run" -p -S - \
        | grep -oP 'https://[a-z0-9-]+\.lhr\.life' | tail -1 || true)
    if [ -z "$TUNNEL_URL" ]; then
        # Fallback to localtunnel
        TUNNEL_URL=$(tmux capture-pane -J -t "$SESSION:localtunnel" -p -S - \
            | grep -oP 'https://[a-z0-9-]+\.loca\.lt' | tail -1 || true)
    fi
    printf "."
done
echo ""

if [ -z "$TUNNEL_URL" ]; then
    err "Tunnel failed to start after ${MAX_WAIT}s"
    warn "You'll need to register the webhook manually once it's up"
    info "Attaching to session anyway..."
    tmux attach -t "$SESSION"
    exit 1
fi

log "Tunnel URL: $TUNNEL_URL"

###############################################################################
# Update site_config.json with new host_name
###############################################################################
info "Updating site_config.json host_name → $TUNNEL_URL"
docker exec "$DOCKER_CONTAINER" bash -c \
    "cd /home/frappe/frappe-bench && bench --site $SITE set-config host_name '$TUNNEL_URL'" \
    2>/dev/null && log "site_config updated" || warn "Failed to update site_config"

###############################################################################
# Register Vobiz webhook
###############################################################################
info "Registering Vobiz webhook..."
RESULT=$(docker exec -w /home/frappe/frappe-bench/sites "$DOCKER_CONTAINER" \
    /home/frappe/frappe-bench/env/bin/python -c \
    "import sys; sys.path.extend(['/home/frappe/frappe-bench/apps/frappe', '/home/frappe/frappe-bench/apps/crm']); import frappe; frappe.init(site='$SITE', sites_path='.'); frappe.connect(); s = frappe.get_single('CRM Vobiz Settings'); print(s.register_webhook('$VOBIZ_APP_ID')); frappe.db.commit()" \
    2>&1) || true

if echo "$RESULT" | grep -qi "success\|registered\|webhook_url"; then
    log "Vobiz webhook registered successfully!"
else
    warn "Webhook registration output: $RESULT"
    warn "You may need to register manually"
fi

###############################################################################
# Summary
###############################################################################
echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  CRM Development Environment Ready!${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
echo -e "  Dev server:    ${GREEN}http://localhost:8085${NC}"
echo -e "  Tunnel URL:    ${GREEN}$TUNNEL_URL${NC}"
echo -e "  Vobiz webhook: ${GREEN}registered${NC}"
echo -e ""
echo -e "  tmux windows:"
echo -e "    ${CYAN}Ctrl+B 0${NC} → dev server"
echo -e "    ${CYAN}Ctrl+B 1${NC} → localtunnel"
echo -e "    ${CYAN}Ctrl+B 2${NC} → localhost.run"
echo -e "    ${CYAN}Ctrl+B d${NC} → detach (keeps running)"
echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
echo ""

# Attach to session
tmux attach -t "$SESSION"
