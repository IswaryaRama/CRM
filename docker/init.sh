#!bin/bash

if [ -d "/home/frappe/frappe-bench/apps/frappe" ]; then
    echo "Bench already exists, skipping init"
    cd frappe-bench
    bench start
else
    echo "Creating new bench..."
fi

bench init --skip-redis-config-generation frappe-bench --version version-15

cd frappe-bench

# Use containers instead of localhost
bench set-mariadb-host mariadb
bench set-redis-cache-host redis://redis:6379
bench set-redis-queue-host redis://redis:6379
bench set-redis-socketio-host redis://redis:6379

# Remove redis, watch from Procfile
sed -i '/redis/d' ./Procfile
sed -i '/watch/d' ./Procfile

ln -sf /workspace /home/frappe/frappe-bench/apps/crm
/home/frappe/frappe-bench/env/bin/pip install -e /workspace
printf "\ncrm\n" >> /home/frappe/frappe-bench/sites/apps.txt

bench new-site crm.aiprof.com \
    --force \
    --mariadb-root-password 123 \
    --admin-password admin \
    --no-mariadb-socket

bench --site crm.aiprof.com install-app crm
bench --site crm.aiprof.com set-config developer_mode 1
bench --site crm.aiprof.com set-config mute_emails 1
bench --site crm.aiprof.com set-config server_script_enabled 1
bench --site crm.aiprof.com clear-cache
bench use crm.aiprof.com

bench start
