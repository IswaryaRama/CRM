import frappe

def test():
    frappe.set_user("Administrator")
    print("Testing data import insert...")
    try:
        doc = frappe.get_doc({
            "doctype": "Data Import",
            "reference_doctype": "CRM Lead",
            "import_type": "Insert New Records",
            "status": "Pending"
        })
        doc.insert()
        print("Success! Inserted:", doc.name)
        frappe.db.rollback()
    except Exception as e:
        import traceback
        traceback.print_exc()
