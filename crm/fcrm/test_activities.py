import frappe
from crm.api.session import get_users

def run():
	users, crm_users = get_users()
	for u in crm_users:
		print("CRM USER:", repr(u.name), "FULL NAME:", repr(u.full_name), "EMAIL:", repr(u.email))
	for u in users:
		print("USER:", repr(u.name), "FULL NAME:", repr(u.full_name), "EMAIL:", repr(u.email))
