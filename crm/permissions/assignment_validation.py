import frappe
from frappe import _
from crm.permissions.org_hierarchy import hierarchy_enabled, _team_mem_query

def validate_assignment(doc, method=None):
	if not hierarchy_enabled():
		return
		
	user = frappe.session.user
	if user == "Administrator" or "System Manager" in frappe.get_roles(user):
		return
		
	if doc.doctype == "CRM Lead":
		owner_field = "lead_owner"
	elif doc.doctype == "CRM Deal":
		owner_field = "deal_owner"
	elif doc.doctype == "ToDo":
		owner_field = "allocated_to"
		# Only check ToDos linked to Lead or Deal
		if doc.reference_type not in ["CRM Lead", "CRM Deal"]:
			return
	else:
		return
		
	new_owner = doc.get(owner_field)
	
	if not new_owner:
		return
		
	if doc.is_new():
		old_owner = None
	else:
		old_owner = frappe.db.get_value(doc.doctype, doc.name, owner_field)
		
	if new_owner == old_owner:
		return
		
	roles = frappe.get_roles(user)
	
	if "Sales Manager" in roles:
		if new_owner == user:
			return
			
		team_members = [row.user for row in _team_mem_query(user).run(as_dict=True)]
		if new_owner not in team_members:
			frappe.throw(_("Sales Managers can only assign records to themselves or their team members."))
			
	elif "Sales User" in roles:
		if new_owner != user:
			frappe.throw(_("Sales Users cannot assign records to other users."))
