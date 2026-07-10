import frappe

def check():
	print("--- CRM Call Log List ---")
	logs = frappe.get_all("CRM Call Log", fields=["name", "type", "from", "to", "status", "creation", "reference_doctype", "reference_docname"])
	print(f"Total Call Logs in MariaDB: {len(logs)}")
	for log in logs:
		print(log)
