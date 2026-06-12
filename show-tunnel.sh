#!/usr/bin/env bash
# Helper script to quickly show or override the active Vobiz public tunnel URL

SESSION="crm"
DOCKER_CONTAINER="crm-frappe-1"
SITE="crm.localhost"
VOBIZ_APP_ID="12995932524652812"

# Check if docker container is running
if ! docker ps --format '{{.Names}}' | grep -q "^${DOCKER_CONTAINER}$"; then
    echo "Docker container '${DOCKER_CONTAINER}' is not running."
    exit 1
fi

# If an argument is passed, update the webhook URL in settings and register it with Vobiz
if [ -n "${1:-}" ]; then
    OVERRIDE_URL="$1"
    echo "Updating Webhook URL Override in CRM Vobiz Settings to: ${OVERRIDE_URL}"
    
    # Remove trailing slash if present
    OVERRIDE_URL=$(echo "$OVERRIDE_URL" | sed 's/\/$//')
    
    RESULT=$(docker exec -w /home/frappe/frappe-bench/sites "$DOCKER_CONTAINER" \
        /home/frappe/frappe-bench/env/bin/python -c \
        "import sys; sys.path.extend(['/home/frappe/frappe-bench/apps/frappe', '/home/frappe/frappe-bench/apps/crm']); import frappe; frappe.init(site='$SITE', sites_path='.'); frappe.connect(); s = frappe.get_single('CRM Vobiz Settings'); s.webhook_url_override = '$OVERRIDE_URL'; s.save(); frappe.db.commit(); print(s.register_webhook('$VOBIZ_APP_ID')); frappe.db.commit()" \
        2>&1) || true
        
    if echo "$RESULT" | grep -qi "success\|registered\|webhook_url"; then
        echo "Vobiz webhook registered successfully with override!"
        echo "Active Tunnel URL (Overridden):"
        echo "  $OVERRIDE_URL"
        echo ""
        echo "Webhook Endpoint:"
        echo "  $OVERRIDE_URL/api/method/crm.integrations.vobiz.api.voice"
        exit 0
    else
        echo "Failed to register webhook. Output:"
        echo "$RESULT"
        exit 1
    fi
fi

# If no argument is passed, check if there is an override in the database first
DB_OVERRIDE=$(docker exec -w /home/frappe/frappe-bench/sites "$DOCKER_CONTAINER" \
    /home/frappe/frappe-bench/env/bin/python -c \
    "import sys; sys.path.extend(['/home/frappe/frappe-bench/apps/frappe', '/home/frappe/frappe-bench/apps/crm']); import frappe; frappe.init(site='$SITE', sites_path='.'); frappe.connect(); print(frappe.db.get_single_value('CRM Vobiz Settings', 'webhook_url_override') or '')" \
    2>/dev/null | xargs)

if [ -n "$DB_OVERRIDE" ]; then
    echo "Active Tunnel URL (Overridden in CRM Vobiz Settings):"
    echo "  $DB_OVERRIDE"
    echo ""
    echo "Webhook Endpoint:"
    echo "  $DB_OVERRIDE/api/method/crm.integrations.vobiz.api.voice"
    exit 0
fi

if ! tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "tmux session '$SESSION' is not running."
    echo "Please start the dev environment first: ./start-crm.sh"
    exit 1
fi

# Try to find localhost.run URL first (Window 2)
URL=$(tmux capture-pane -J -t "$SESSION:2" -p -S -200 2>/dev/null \
    | grep -oP 'https://[a-z0-9-]+\.lhr\.life' | tail -1 || true)

if [ -n "$URL" ]; then
    echo "Active Tunnel URL (localhost.run):"
    echo "  $URL"
    echo ""
    echo "Webhook Endpoint:"
    echo "  $URL/api/method/crm.integrations.vobiz.api.voice"
    exit 0
fi

# Fallback to localtunnel URL (Window 1)
URL=$(tmux capture-pane -J -t "$SESSION:1" -p -S -200 2>/dev/null \
    | grep -oP 'https://[a-z0-9-]+\.loca\.lt' | tail -1 || true)

if [ -n "$URL" ]; then
    echo "Active Tunnel URL (localtunnel):"
    echo "  $URL"
    echo ""
    echo "Webhook Endpoint:"
    echo "  $URL/api/method/crm.integrations.vobiz.api.voice"
    exit 0
fi

echo "No active tunnel URL found in tmux session."
echo "Check your tunnels in tmux: tmux attach -t $SESSION"
exit 1
