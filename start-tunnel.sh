#!/bin/bash

echo "Starting localtunnel on port 8005..."
# Start localtunnel in the background and redirect output to a file
> .tunnel_output.log
npx localtunnel --port 8005 > .tunnel_output.log &
TUNNEL_PID=$!

echo "Waiting for tunnel URL..."
TUNNEL_URL=""
for i in {1..15}; do
    sleep 1
    TUNNEL_URL=$(grep -o 'https://.*\.loca\.lt' .tunnel_output.log | head -n 1)
    if [ -n "$TUNNEL_URL" ]; then
        break
    fi
done

if [ -z "$TUNNEL_URL" ]; then
    echo "Failed to get tunnel URL after 15 seconds. Please check your internet or try again."
    kill $TUNNEL_PID
    exit 1
fi

echo "Tunnel successfully started at: $TUNNEL_URL"
echo "Auto-registering webhook in Frappe..."

# Run python script inside docker to update and register the webhook
docker exec crm-frappe-1 bash -c "cd /home/frappe/frappe-bench/sites && /home/frappe/frappe-bench/env/bin/python -c '
import frappe
frappe.init(site=\"crm.localhost\")
frappe.connect()
s = frappe.get_single(\"CRM Vobiz Settings\")
s.webhook_url_override = \"$TUNNEL_URL\"
s.save(ignore_permissions=True)
frappe.db.commit()

if s.app_id:
    try:
        s.register_webhook(s.app_id)
        print(\"✅ Successfully auto-registered Vobiz webhook to: $TUNNEL_URL\")
    except Exception as e:
        print(\"❌ Failed to register webhook with Vobiz:\", e)
else:
    print(\"⚠️ Tunnel saved, but no Vobiz Application selected. Please select one in the Telephony settings UI.\")
'"

echo "Tunnel is running! Press Ctrl+C to stop."
# Keep the script running to keep the tunnel alive
wait $TUNNEL_PID
