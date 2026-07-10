import frappe
frappe.init(site="crm.aiprof.com", sites_path="/home/frappe/frappe-bench/sites")
frappe.connect()

pending_imports = frappe.db.get_all("Data Import", filters={"status": ["in", ["Pending", "Partial Success"]]}, fields=["name", "status"], order_by="creation desc")

if not pending_imports:
    print("No pending imports found! They must have all completed.")
else:
    for doc in pending_imports:
        print(f"Starting import for {doc.name}")
        di = frappe.get_doc("Data Import", doc.name)
        di.start_import()
        frappe.db.commit()
        print(f"Import triggered for {doc.name}")
