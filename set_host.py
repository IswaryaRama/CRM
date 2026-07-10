import json

filepath = '/home/frappe/frappe-bench/sites/common_site_config.json'
with open(filepath, 'r') as f:
    data = json.load(f)

data['host_name'] = 'https://crm.aiprof.com'

with open(filepath, 'w') as f:
    json.dump(data, f, indent=1)

print("Updated host_name")
