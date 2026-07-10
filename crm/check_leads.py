import frappe

def run():
    leads = frappe.get_all('CRM Lead', filters={'first_name': ['in', ['Harini', 'Janu', 'Ramu', 'Lalitha', 'Lilly']]}, fields=['name', 'first_name', 'lead_owner', '_assign'])
    for l in leads:
        print(l)
