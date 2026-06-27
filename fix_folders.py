import frappe
from frappe.core.doctype.file.file import setup_folder_path
def run():
    if not frappe.db.exists("File", "Home"):
        frappe.get_doc({
            "doctype": "File",
            "file_name": "Home",
            "is_folder": 1
        }).insert(ignore_permissions=True)
    if not frappe.db.exists("File", "Home/Attachments"):
        frappe.get_doc({
            "doctype": "File",
            "file_name": "Attachments",
            "folder": "Home",
            "is_folder": 1
        }).insert(ignore_permissions=True)
    frappe.db.commit()
    print("Folders fixed")
run()
