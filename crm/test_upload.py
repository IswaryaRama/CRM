import frappe

def run():
    try:
        doc = frappe.get_doc({
            "doctype": "File",
            "file_name": "test_upload.txt",
            "content": "test",
            "is_private": 1
        })
        doc.insert(ignore_permissions=True)
        print(f"Success! File created: {doc.name}")
        frappe.db.commit()
    except Exception as e:
        import traceback
        traceback.print_exc()
