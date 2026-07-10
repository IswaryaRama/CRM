import frappe
from crm.fcrm.doctype.crm_fields_layout.crm_fields_layout import get_fields_layout
def check():
    layout = get_fields_layout(doctype='CRM Lead', type='Quick Entry')
    print("API returns:")
    print(layout)

check()
