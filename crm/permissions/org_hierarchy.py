# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.utils.caching import request_cache

_OWNER_FIELD = {
	"CRM Lead": "lead_owner",
	"CRM Deal": "deal_owner",
}


def hierarchy_enabled() -> bool:
	return bool(frappe.db.get_single_value("FCRM Settings", "enable_sales_hierarchy"))


def _permission_query_conditions(user: str | None, doctype: str):
	if not user:
		user = frappe.session.user

	if user == "Administrator":
		return ""

	roles = frappe.get_roles(user)
	if "System Manager" in roles:
		return ""

	if not hierarchy_enabled():
		owner_field = _OWNER_FIELD[doctype]
		DT = frappe.qb.DocType(doctype)
		Todo = frappe.qb.DocType("ToDo").as_("_todo")
		q1 = (DT[owner_field] == user) | (DT.owner == user)
		q2 = DT.name.isin(
			frappe.qb.from_(Todo)
			.select(Todo.reference_name)
			.where(
				(Todo.reference_type == doctype)
				& (Todo.status != "Cancelled")
				& ((Todo.allocated_to == user) | (Todo.assigned_by == user) | (Todo.owner == user))
			)
		)
		return q1 | q2

	owner_field = _OWNER_FIELD[doctype]
	DT = frappe.qb.DocType(doctype)
	Todo = frappe.qb.DocType("ToDo").as_("_todo")

	if "Sales Manager" in roles:
		# Owner is the user themselves or any member reporting to them
		q1 = (
			(DT[owner_field] == user)
			| (DT.owner == user)
			| DT[owner_field].isin(_team_mem_query(user))
			| DT.owner.isin(_team_mem_query(user))
		)
		# Assigned to the user or any member reporting to them by ToDo
		q2 = DT.name.isin(
			frappe.qb.from_(Todo)
			.select(Todo.reference_name)
			.where(
				(Todo.reference_type == doctype)
				& (Todo.status != "Cancelled")
				& (
					(Todo.allocated_to == user)
					| (Todo.allocated_to.isin(_team_mem_query(user)))
					| (Todo.assigned_by == user)
					| (Todo.assigned_by.isin(_team_mem_query(user)))
					| (Todo.owner == user)
					| (Todo.owner.isin(_team_mem_query(user)))
				)
			)
		)
		return q1 | q2

	# Sales User: own records and records directly assigned to them or by them
	q1 = (DT[owner_field] == user) | (DT.owner == user)
	q2 = DT.name.isin(
		frappe.qb.from_(Todo)
		.select(Todo.reference_name)
		.where(
			(Todo.reference_type == doctype)
			& (Todo.status != "Cancelled")
			& ((Todo.allocated_to == user) | (Todo.assigned_by == user) | (Todo.owner == user))
		)
	)
	return q1 | q2


def get_lead_permission_query_conditions(user=None):
	cond = _permission_query_conditions(user, "CRM Lead")
	return cond.get_sql(quote_char="`", secondary_quote_char="'") if cond else ""


def get_deal_permission_query_conditions(user=None):
	cond = _permission_query_conditions(user, "CRM Deal")
	return cond.get_sql(quote_char="`", secondary_quote_char="'") if cond else ""


def _has_permission(doc, ptype, user, doctype: str) -> bool | None:
	if not doc or isinstance(doc, str):
		return True

	if not user:
		user = frappe.session.user

	if user == "Administrator":
		return True

	roles = frappe.get_roles(user)
	if "System Manager" in roles:
		return True

	conditions = _permission_query_conditions(user, doctype)
	DT = frappe.qb.DocType(doctype)
	return bool(
		frappe.qb.from_(DT).select(DT.name).where(DT.name == doc.name).where(conditions).limit(1).run()
	)


def has_lead_permission(doc, ptype, user):
	return _has_permission(doc, ptype, user, "CRM Lead")


def has_deal_permission(doc, ptype, user):
	return _has_permission(doc, ptype, user, "CRM Deal")


def _in_hierarchy(user: str) -> bool:
	return bool(frappe.db.get_value("User", user, "reports_to") or frappe.db.exists("User", {"reports_to": user}))


def _team_mem_query(user: str):
	User = frappe.qb.DocType("User")
	return (
		frappe.qb.from_(User)
		.select(User.name.as_("user"))
		.where((User.name == user) | (User.reports_to == user))
	)

def _activity_query_conditions(user, doctype):
	if not user:
		user = frappe.session.user

	if user == "Administrator":
		return ""

	roles = frappe.get_roles(user)
	if "System Manager" in roles:
		return ""

	DT = frappe.qb.DocType(doctype)
	Lead = frappe.qb.DocType("CRM Lead")
	Deal = frappe.qb.DocType("CRM Deal")
	
	lead_cond = _permission_query_conditions(user, "CRM Lead")
	deal_cond = _permission_query_conditions(user, "CRM Deal")
	
	q = DT.owner == user
	if lead_cond:
		q = q | ((DT.reference_doctype == "CRM Lead") & DT.reference_docname.isin(
			frappe.qb.from_(Lead).select(Lead.name).where(lead_cond)
		))
	if deal_cond:
		q = q | ((DT.reference_doctype == "CRM Deal") & DT.reference_docname.isin(
			frappe.qb.from_(Deal).select(Deal.name).where(deal_cond)
		))
	return q

def get_note_permission_query_conditions(user=None):
	cond = _activity_query_conditions(user, "FCRM Note")
	return cond.get_sql(quote_char="`", secondary_quote_char="'") if cond else ""

def get_task_permission_query_conditions(user=None):
	cond = _activity_query_conditions(user, "CRM Task")
	return cond.get_sql(quote_char="`", secondary_quote_char="'") if cond else ""

def get_call_log_permission_query_conditions(user=None):
	cond = _activity_query_conditions(user, "CRM Call Log")
	return cond.get_sql(quote_char="`", secondary_quote_char="'") if cond else ""

def _has_activity_permission(doc, ptype, user, doctype):
	if not doc or isinstance(doc, str):
		return True

	if not user:
		user = frappe.session.user

	if user == "Administrator":
		return True

	roles = frappe.get_roles(user)
	if "System Manager" in roles:
		return True

	if doc.owner == user:
		return True

	if doc.get("reference_doctype") == "CRM Lead" and doc.get("reference_docname"):
		if frappe.db.exists("CRM Lead", doc.reference_docname):
			return has_lead_permission(frappe.get_doc("CRM Lead", doc.reference_docname), ptype, user)
		
	if doc.get("reference_doctype") == "CRM Deal" and doc.get("reference_docname"):
		if frappe.db.exists("CRM Deal", doc.reference_docname):
			return has_deal_permission(frappe.get_doc("CRM Deal", doc.reference_docname), ptype, user)

	return False

def has_note_permission(doc, ptype, user=None):
	return _has_activity_permission(doc, ptype, user, "FCRM Note")

def has_task_permission(doc, ptype, user=None):
	return _has_activity_permission(doc, ptype, user, "CRM Task")

def has_call_log_permission(doc, ptype, user=None):
	return _has_activity_permission(doc, ptype, user, "CRM Call Log")

def get_reporting_users(user: str) -> list[str]:
	"""Get all users reporting to the given user (directly or indirectly)."""
	users = [user]
	direct_reports = frappe.get_all("User", filters={"reports_to": user, "enabled": 1}, pluck="name")
	for report in direct_reports:
		if report not in users:
			users.extend(get_reporting_users(report))
	seen = set()
	return [u for u in users if not (u in seen or seen.add(u))]
