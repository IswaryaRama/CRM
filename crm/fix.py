import frappe

def run():
    frappe.db.sql("""DELETE FROM `tabCRM View Settings` WHERE dt='CRM Lead' AND type='list'""")
    frappe.db.commit()
    print("Deleted CRM View Settings for CRM Lead list")





