import os

filepath = '/home/frappe/frappe-bench/apps/frappe/frappe/core/doctype/data_import/data_import.py'

with open(filepath, 'r') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if line.startswith('def form_start_import'):
        # Check if the previous line is already the whitelist decorator
        if len(new_lines) == 0 or '@frappe.whitelist()' not in new_lines[-1]:
            new_lines.append('@frappe.whitelist()\n')
    new_lines.append(line)

with open(filepath, 'w') as f:
    f.writelines(new_lines)

print("Patched data_import.py successfully!")
