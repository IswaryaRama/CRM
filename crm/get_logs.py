import frappe
import json

def check_all():
    errors = frappe.get_all('Error Log', fields=['name', 'method', 'error', 'creation'], limit=5, order_by='creation desc')
    print("=== LATEST ERROR LOGS ===")
    for e in errors:
        print(f"Error {e.name} at {e.creation} in {e.method}:")
        print(e.error[:200] + "..." if getattr(e, 'error', None) else "No error text")
        print("---")
        
    messages = frappe.get_all('WhatsApp Message', fields=['name', 'status', 'to', 'message_id', 'creation'], limit=5, order_by='creation desc')
    print("\n=== LATEST WA MESSAGES ===")
    for m in messages:
        print(f"{m.name}: {m.status} to {m.to} (wamid: {m.message_id}) at {m.creation}")
