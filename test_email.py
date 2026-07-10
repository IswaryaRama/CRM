import frappe
frappe.init(site="crm.localhost")
frappe.connect()
frappe.set_user("Administrator")
try:
    frappe.call("frappe.core.doctype.communication.email.make", recipients="test@example.com", subject="Test", content="Test", doctype="CRM Lead", name="", send_email=1, sender="someuser@example.com")
except Exception as e:
    print("ERROR:", e)
