import frappe

def test():
    user = "iswaryagajjala@gmail.com"
    frappe.set_user(user)
    print("Testing permission as", user)
    try:
        print("has_permission:", frappe.has_permission("CRM Lead", "import"))
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
