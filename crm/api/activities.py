import json

import frappe
from bs4 import BeautifulSoup
from frappe import _
from frappe.desk.form.load import get_docinfo
from frappe.query_builder import JoinType
from frappe.translate import get_translated_doctypes

from crm.fcrm.doctype.crm_call_log.crm_call_log import parse_call_log


@frappe.whitelist()
def get_activities(name: str):
	if frappe.db.exists("CRM Deal", name):
		return get_deal_activities(name)
	elif frappe.db.exists("CRM Lead", name):
		return get_lead_activities(name)
	else:
		frappe.throw(_("Document not found"), frappe.DoesNotExistError)


def get_deal_activities(name: str):
	if not frappe.has_permission("CRM Deal", "read", name):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	get_docinfo("", "CRM Deal", name)
	docinfo = frappe.response["docinfo"]
	deal_meta = frappe.get_meta("CRM Deal")
	deal_fields = {
		field.fieldname: {"label": field.label, "options": field.options} for field in deal_meta.fields
	}
	avoid_fields = [
		"lead",
		"response_by",
		"sla_creation",
		"sla",
		"first_response_time",
		"first_responded_on",
	]

	doc = frappe.db.get_values("CRM Deal", name, ["creation", "owner", "lead"])[0]
	lead = doc[2]

	activities = []
	calls = []
	notes = []
	tasks = []
	attachments = []
	creation_text = _("created this deal")

	if lead:
		activities, calls, notes, tasks, attachments = get_lead_activities(lead)
		creation_text = _("converted the lead to this deal")

	activities.append(
		{
			"activity_type": "creation",
			"creation": doc[0],
			"owner": doc[1],
			"data": creation_text,
			"is_lead": False,
		}
	)

	docinfo.versions.reverse()

	for version in docinfo.versions:
		data = json.loads(version.data)
		if not data.get("changed"):
			continue

		if change := data.get("changed")[0]:
			field = deal_fields.get(change[0], None)

			if not field or change[0] in avoid_fields or (not change[1] and not change[2]):
				continue

			field_label = field.get("label") or change[0]
			field_option = field.get("options") or None

			activity_type = "changed"
			data = {
				"field": change[0],
				"field_label": field_label,
				"old_value": change[1],
				"value": change[2],
			}

			if not change[1] and change[2]:
				activity_type = "added"
				data = {
					"field": change[0],
					"field_label": field_label,
					"value": change[2],
				}
			elif change[1] and not change[2]:
				activity_type = "removed"
				data = {
					"field": change[0],
					"field_label": field_label,
					"value": change[1],
				}

			if data.get("value") and field_option and is_translatable(field_option):
				data["value"] = _(data["value"])

				if data.get("old_value"):
					data["old_value"] = _(data["old_value"])

		activity = {
			"activity_type": activity_type,
			"creation": version.creation,
			"owner": version.owner,
			"data": data,
			"is_lead": False,
			"options": field_option,
		}
		activities.append(activity)

	for comment in docinfo.comments:
		activity = {
			"name": comment.name,
			"activity_type": "comment",
			"creation": comment.creation,
			"owner": comment.owner,
			"content": comment.content,
			"attachments": get_attachments("Comment", comment.name),
			"is_lead": False,
		}
		activities.append(activity)

	for communication in docinfo.communications + docinfo.automated_messages:
		activity = {
			"activity_type": "communication",
			"communication_type": communication.communication_type,
			"communication_date": communication.communication_date or communication.creation,
			"creation": communication.creation,
			"data": {
				"subject": communication.subject,
				"content": communication.content,
				"sender_full_name": communication.sender_full_name,
				"sender": communication.sender,
				"recipients": communication.recipients,
				"cc": communication.cc,
				"bcc": communication.bcc,
				"attachments": get_attachments("Communication", communication.name),
				"read_by_recipient": communication.read_by_recipient,
				"delivery_status": communication.delivery_status,
			},
			"is_lead": False,
		}
		activities.append(activity)

	for attachment_log in docinfo.attachment_logs:
		activity = {
			"name": attachment_log.name,
			"activity_type": "attachment_log",
			"creation": attachment_log.creation,
			"owner": attachment_log.owner,
			"data": parse_attachment_log(attachment_log.content, attachment_log.comment_type),
			"is_lead": False,
		}
		activities.append(activity)

	deal_calls = get_linked_calls(name).get("calls", [])
	calls = calls + deal_calls
	notes = notes + get_linked_notes(name) + get_linked_calls(name).get("notes", [])
	tasks = tasks + get_linked_tasks(name) + get_linked_calls(name).get("tasks", [])
	attachments = attachments + get_attachments("CRM Deal", name)

	call_names = [call.name for call in deal_calls] if deal_calls else []
	if call_names:
		attachments = attachments + (frappe.db.get_all(
			"File",
			filters={"attached_to_doctype": "CRM Call Log", "attached_to_name": ["in", call_names]},
			fields=[
				"name",
				"file_name",
				"file_type",
				"file_url",
				"file_size",
				"is_private",
				"modified",
				"creation",
				"owner",
			],
		) or [])

	activities.sort(key=lambda x: x["creation"], reverse=True)
	activities = handle_multiple_versions(activities)

	return activities, calls, notes, tasks, attachments


def get_lead_activities(name: str):
	if not frappe.has_permission("CRM Lead", "read", name):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	get_docinfo("", "CRM Lead", name)
	docinfo = frappe.response["docinfo"]
	lead_meta = frappe.get_meta("CRM Lead")
	lead_fields = {
		field.fieldname: {"label": field.label, "options": field.options} for field in lead_meta.fields
	}
	avoid_fields = [
		"converted",
		"response_by",
		"sla_creation",
		"sla",
		"first_response_time",
		"first_responded_on",
	]

	doc = frappe.db.get_values("CRM Lead", name, ["creation", "owner"])[0]
	activities = [
		{
			"activity_type": "creation",
			"creation": doc[0],
			"owner": doc[1],
			"data": _("created this lead"),
			"is_lead": True,
		}
	]

	docinfo.versions.reverse()

	for version in docinfo.versions:
		data = json.loads(version.data)
		if not data.get("changed"):
			continue

		if change := data.get("changed")[0]:
			field = lead_fields.get(change[0], None)

			if not field or change[0] in avoid_fields or (not change[1] and not change[2]):
				continue

			field_label = field.get("label") or change[0]
			field_option = field.get("options") or None

			activity_type = "changed"
			data = {
				"field": change[0],
				"field_label": field_label,
				"old_value": change[1],
				"value": change[2],
			}

			if not change[1] and change[2]:
				activity_type = "added"
				data = {
					"field": change[0],
					"field_label": field_label,
					"value": change[2],
				}
			elif change[1] and not change[2]:
				activity_type = "removed"
				data = {
					"field": change[0],
					"field_label": field_label,
					"value": change[1],
				}

			if data.get("value") and field_option and is_translatable(field_option):
				data["value"] = _(data["value"])

				if data.get("old_value"):
					data["old_value"] = _(data["old_value"])

		activity = {
			"activity_type": activity_type,
			"creation": version.creation,
			"owner": version.owner,
			"data": data,
			"is_lead": True,
			"options": field_option,
		}
		activities.append(activity)

	for comment in docinfo.comments:
		activity = {
			"name": comment.name,
			"activity_type": "comment",
			"creation": comment.creation,
			"owner": comment.owner,
			"content": comment.content,
			"attachments": get_attachments("Comment", comment.name),
			"is_lead": True,
		}
		activities.append(activity)

	for communication in docinfo.communications + docinfo.automated_messages:
		activity = {
			"activity_type": "communication",
			"communication_type": communication.communication_type,
			"communication_date": communication.communication_date or communication.creation,
			"creation": communication.creation,
			"data": {
				"subject": communication.subject,
				"content": communication.content,
				"sender_full_name": communication.sender_full_name,
				"sender": communication.sender,
				"recipients": communication.recipients,
				"cc": communication.cc,
				"bcc": communication.bcc,
				"attachments": get_attachments("Communication", communication.name),
				"read_by_recipient": communication.read_by_recipient,
				"delivery_status": communication.delivery_status,
			},
			"is_lead": True,
		}
		activities.append(activity)

	for attachment_log in docinfo.attachment_logs:
		activity = {
			"name": attachment_log.name,
			"activity_type": "attachment_log",
			"creation": attachment_log.creation,
			"owner": attachment_log.owner,
			"data": parse_attachment_log(attachment_log.content, attachment_log.comment_type),
			"is_lead": True,
		}
		activities.append(activity)

	calls = get_linked_calls(name).get("calls", [])
	notes = get_linked_notes(name) + get_linked_calls(name).get("notes", [])
	tasks = get_linked_tasks(name) + get_linked_calls(name).get("tasks", [])
	attachments = get_attachments("CRM Lead", name)

	call_names = [call.name for call in calls] if calls else []
	if call_names:
		attachments = attachments + (frappe.db.get_all(
			"File",
			filters={"attached_to_doctype": "CRM Call Log", "attached_to_name": ["in", call_names]},
			fields=[
				"name",
				"file_name",
				"file_type",
				"file_url",
				"file_size",
				"is_private",
				"modified",
				"creation",
				"owner",
			],
		) or [])

	activities.sort(key=lambda x: x["creation"], reverse=True)
	activities = handle_multiple_versions(activities)

	return activities, calls, notes, tasks, attachments


def get_attachments(doctype: str, name: str):
	return (
		frappe.db.get_all(
			"File",
			filters={"attached_to_doctype": doctype, "attached_to_name": name},
			fields=[
				"name",
				"file_name",
				"file_type",
				"file_url",
				"file_size",
				"is_private",
				"modified",
				"creation",
				"owner",
			],
		)
		or []
	)


def handle_multiple_versions(versions: list):
	activities = []
	grouped_versions = []
	old_version = None
	for version in versions:
		is_version = version["activity_type"] in ["changed", "added", "removed"]
		if not is_version:
			activities.append(version)
		if not old_version:
			old_version = version
			if is_version:
				grouped_versions.append(version)
			continue
		if is_version and old_version.get("owner") and version["owner"] == old_version["owner"]:
			grouped_versions.append(version)
		else:
			if grouped_versions:
				activities.append(parse_grouped_versions(grouped_versions))
			grouped_versions = []
			if is_version:
				grouped_versions.append(version)
		old_version = version
		if version == versions[-1] and grouped_versions:
			activities.append(parse_grouped_versions(grouped_versions))

	return activities


def parse_grouped_versions(versions: list):
	version = versions[0]
	if len(versions) == 1:
		return version
	other_versions = versions[1:]
	version["other_versions"] = other_versions
	return version


def get_linked_calls(name: str):
	calls = frappe.db.get_all(
		"CRM Call Log",
		filters={"reference_docname": name},
		fields=[
			"name",
			"caller",
			"receiver",
			"from",
			"to",
			"duration",
			"start_time",
			"end_time",
			"status",
			"type",
			"recording_url",
			"creation",
			"note",
		],
	)

	linked_calls = frappe.db.get_all(
		"Dynamic Link", filters={"link_name": name, "parenttype": "CRM Call Log"}, pluck="parent"
	)

	notes = []
	tasks = []

	if linked_calls:
		CallLog = frappe.qb.DocType("CRM Call Log")
		Link = frappe.qb.DocType("Dynamic Link")
		query = (
			frappe.qb.from_(CallLog)
			.select(
				CallLog.name,
				CallLog.caller,
				CallLog.receiver,
				CallLog["from"],
				CallLog.to,
				CallLog.duration,
				CallLog.start_time,
				CallLog.end_time,
				CallLog.status,
				CallLog.type,
				CallLog.recording_url,
				CallLog.creation,
				CallLog.note,
				Link.link_doctype,
				Link.link_name,
			)
			.join(Link, JoinType.inner)
			.on(Link.parent == CallLog.name)
			.where(CallLog.name.isin(linked_calls))
		)
		_calls = query.run(as_dict=True)

		for call in _calls:
			if call.get("link_doctype") == "FCRM Note":
				notes.append(call.link_name)
			elif call.get("link_doctype") == "CRM Task":
				tasks.append(call.link_name)

		_calls = [call for call in _calls if call.get("link_doctype") not in ["FCRM Note", "CRM Task"]]
		if _calls:
			calls = calls + _calls

	if notes:
		notes = frappe.db.get_all(
			"FCRM Note",
			filters={"name": ("in", notes)},
			fields=["name", "title", "content", "owner", "modified"],
		)

	if tasks:
		tasks = frappe.db.get_all(
			"CRM Task",
			filters={"name": ("in", tasks)},
			fields=[
				"name",
				"title",
				"description",
				"assigned_to",
				"due_date",
				"priority",
				"status",
				"modified",
			],
		)

	calls = [parse_call_log(call) for call in calls] if calls else []

	return {"calls": calls, "notes": notes, "tasks": tasks}


def get_linked_notes(name: str):
	notes = frappe.db.get_all(
		"FCRM Note",
		filters={"reference_docname": name},
		fields=["name", "title", "content", "owner", "modified", "creation"],
	)
	return notes or []


def get_linked_tasks(name: str):
	tasks = frappe.db.get_all(
		"CRM Task",
		filters={"reference_docname": name},
		fields=[
			"name",
			"title",
			"description",
			"assigned_to",
			"due_date",
			"priority",
			"status",
			"modified",
			"creation",
		],
	)
	return tasks or []


def parse_attachment_log(html: str, type: str):
	soup = BeautifulSoup(html, "html.parser")
	a_tag = soup.find("a")
	type = "added" if type == "Attachment" else "removed"
	if not a_tag:
		return {
			"type": type,
			"file_name": html.replace("Removed ", ""),
			"file_url": "",
			"is_private": False,
		}

	is_private = False
	if "private/files" in a_tag["href"]:
		is_private = True

	return {
		"type": type,
		"file_name": a_tag.text,
		"file_url": a_tag["href"],
		"is_private": is_private,
	}


def is_translatable(doctype: str) -> bool:
	return doctype in get_translated_doctypes()


@frappe.whitelist()
def get_user_activities(user: str, limit: int = 100):
	# Ensure admin/manager permissions
	roles = frappe.get_roles()
	is_system_manager = "System Manager" in roles
	is_sales_manager = "Sales Manager" in roles and not is_system_manager

	if not is_system_manager and not is_sales_manager:
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	from crm.permissions.org_hierarchy import hierarchy_enabled, get_reporting_users
	if is_sales_manager:
		if hierarchy_enabled():
			allowed = get_reporting_users(frappe.session.user)
			if user not in allowed:
				frappe.throw(_("Not permitted to view this user's activities"), frappe.PermissionError)
		else:
			if user != frappe.session.user:
				frappe.throw(_("Not permitted to view this user's activities"), frappe.PermissionError)

	activities = []

	# 1. Fetch versions (edits/creations)
	versions = frappe.db.get_all(
		"Version",
		filters={"owner": user, "ref_doctype": ["in", ["CRM Lead", "CRM Deal", "Contact", "CRM Organization"]]},
		fields=["name", "ref_doctype", "docname", "data", "creation", "owner"],
		limit=limit,
		order_by="creation desc"
	)
	
	# Resolve doctypes and labels
	lead_meta = frappe.get_meta("CRM Lead")
	lead_fields = {field.fieldname: {"label": field.label, "options": field.options} for field in lead_meta.fields}
	deal_meta = frappe.get_meta("CRM Deal")
	deal_fields = {field.fieldname: {"label": field.label, "options": field.options} for field in deal_meta.fields}
	
	avoid_fields = [
		"converted", "response_by", "sla_creation", "sla", "first_response_time", "first_responded_on",
		"lead", "first_responded_on"
	]

	for v in versions:
		try:
			data = json.loads(v.data)
		except Exception:
			continue
			
		if not data.get("changed"):
			activities.append({
				"activity_type": "creation",
				"creation": v.creation,
				"owner": v.owner,
				"data": _("created this {0}").format(v.ref_doctype),
				"reference_doctype": v.ref_doctype,
				"reference_docname": v.docname
			})
			continue

		if change := data.get("changed")[0]:
			fields_meta = lead_fields if v.ref_doctype == "CRM Lead" else deal_fields
			field = fields_meta.get(change[0], None)
			if not field or change[0] in avoid_fields or (not change[1] and not change[2]):
				continue
				
			field_label = field.get("label") or change[0]
			field_option = field.get("options") or None
			
			activity_type = "changed"
			act_data = {
				"field": change[0],
				"field_label": field_label,
				"old_value": change[1],
				"value": change[2],
			}
			if not change[1] and change[2]:
				activity_type = "added"
				act_data = {
					"field": change[0],
					"field_label": field_label,
					"value": change[2],
				}
			elif change[1] and not change[2]:
				activity_type = "removed"
				act_data = {
					"field": change[0],
					"field_label": field_label,
					"value": change[1],
				}
				
			activities.append({
				"activity_type": activity_type,
				"creation": v.creation,
				"owner": v.owner,
				"data": act_data,
				"reference_doctype": v.ref_doctype,
				"reference_docname": v.docname,
				"options": field_option
			})

	# 2. Fetch comments
	comments = frappe.db.get_all(
		"Comment",
		filters={
			"owner": user,
			"comment_type": "Comment",
			"reference_doctype": ["in", ["CRM Lead", "CRM Deal", "Contact", "CRM Organization", "CRM Call Log"]]
		},
		fields=["name", "reference_doctype", "reference_name", "content", "creation", "owner"],
		limit=limit,
		order_by="creation desc"
	)
	for c in comments:
		ref_doctype = c.reference_doctype
		ref_docname = c.reference_name
		if ref_doctype == "CRM Call Log":
			call_log = frappe.db.get_values("CRM Call Log", ref_docname, ["reference_doctype", "reference_docname"])
			if call_log and call_log[0][0] and call_log[0][1]:
				ref_doctype = call_log[0][0]
				ref_docname = call_log[0][1]
			else:
				links = frappe.db.get_all("Dynamic Link", filters={"parent": ref_docname, "parenttype": "CRM Call Log"}, fields=["link_doctype", "link_name"])
				resolved = False
				for link in links:
					if link.link_doctype in ["CRM Lead", "CRM Deal", "Contact", "CRM Organization"]:
						ref_doctype = link.link_doctype
						ref_docname = link.link_name
						resolved = True
						break
				if not resolved:
					ref_doctype = "CRM Lead"

		activities.append({
			"name": c.name,
			"activity_type": "comment",
			"creation": c.creation,
			"owner": c.owner,
			"content": c.content,
			"reference_doctype": ref_doctype,
			"reference_docname": ref_docname
		})

	# 3. Fetch call logs
	calls = frappe.db.get_all(
		"CRM Call Log",
		or_filters={"owner": user, "caller": user, "receiver": user},
		fields=[
			"name", "caller", "receiver", "from", "to", "duration",
			"start_time", "end_time", "status", "type", "recording_url",
			"creation", "reference_doctype", "reference_docname"
		],
		limit=limit,
		order_by="creation desc"
	)
	for call_log in calls:
		ref_doctype = call_log.reference_doctype
		ref_docname = call_log.reference_docname
		if not ref_doctype or not ref_docname:
			call_log_links = frappe.db.get_all(
				"Dynamic Link", 
				filters={"parent": call_log.name, "parenttype": "CRM Call Log"}, 
				fields=["link_doctype", "link_name"]
			)
			for link in call_log_links:
				if link.link_doctype in ["CRM Lead", "CRM Deal", "Contact", "CRM Organization"]:
					ref_doctype = link.link_doctype
					ref_docname = link.link_name
					break
		if not ref_doctype or not ref_docname:
			ref_doctype = "CRM Lead"
			ref_docname = ""

		activities.append({
			"name": call_log.name,
			"activity_type": "incoming_call" if call_log.type == "Incoming" else "outgoing_call",
			"creation": call_log.creation,
			"owner": user,
			"data": {
				"status": call_log.status,
				"duration": call_log.duration,
				"caller": call_log.caller,
				"receiver": call_log.receiver
			},
			"reference_doctype": ref_doctype,
			"reference_docname": ref_docname
		})

	# 4. Fetch notes
	notes = frappe.db.get_all(
		"FCRM Note",
		filters={"owner": user},
		fields=["name", "title", "content", "owner", "creation", "reference_doctype", "reference_docname"],
		limit=limit,
		order_by="creation desc"
	)
	for note in notes:
		activities.append({
			"name": note.name,
			"activity_type": "note",
			"creation": note.creation,
			"owner": note.owner,
			"title": note.title,
			"content": note.content,
			"reference_doctype": note.reference_doctype or "CRM Lead",
			"reference_docname": note.reference_docname
		})

	# 5. Fetch communications (emails)
	communications = frappe.db.get_all(
		"Communication",
		filters={"reference_doctype": ["in", ["CRM Lead", "CRM Deal", "Contact", "CRM Organization"]]},
		or_filters={"sender": user, "owner": user},
		fields=[
			"name", "communication_type", "communication_date", "creation", "subject", "content",
			"sender_full_name", "sender", "recipients", "cc", "bcc", "read_by_recipient",
			"delivery_status", "reference_doctype", "reference_name"
		],
		limit=limit,
		order_by="creation desc"
	)
	for comm in communications:
		activities.append({
			"name": comm.name,
			"activity_type": "communication",
			"communication_type": comm.communication_type,
			"communication_date": comm.communication_date or comm.creation,
			"creation": comm.creation,
			"data": {
				"subject": comm.subject,
				"content": comm.content,
				"sender_full_name": comm.sender_full_name,
				"sender": comm.sender,
				"recipients": comm.recipients,
				"cc": comm.cc,
				"bcc": comm.bcc,
				"read_by_recipient": comm.read_by_recipient,
				"delivery_status": comm.delivery_status,
			},
			"reference_doctype": comm.reference_doctype,
			"reference_docname": comm.reference_name
		})

	# 6. Fetch WhatsApp messages
	if frappe.db.exists("DocType", "WhatsApp Message"):
		whatsapp = frappe.db.get_all(
			"WhatsApp Message",
			filters={"owner": user},
			fields=[
				"name", "type", "to", "from", "content_type", "message_type",
				"attach", "creation", "message", "status", "reference_doctype", "reference_name"
			],
			limit=limit,
			order_by="creation desc"
		)
		for wa in whatsapp:
			activities.append({
				"name": wa.name,
				"activity_type": "whatsapp",
				"creation": wa.creation,
				"owner": user,
				"data": {
					"type": wa.type,
					"to": wa.to,
					"from": wa.get("from"),
					"content_type": wa.content_type,
					"message_type": wa.message_type,
					"attach": wa.attach,
					"message": wa.message,
					"status": wa.status
				},
				"reference_doctype": wa.reference_doctype or "CRM Lead",
				"reference_docname": wa.reference_name
			})

	# 7. Fetch tasks
	tasks = frappe.db.get_all(
		"CRM Task",
		or_filters={"owner": user, "assigned_to": user},
		fields=[
			"name", "title", "description", "assigned_to", "due_date", "priority",
			"status", "creation", "reference_doctype", "reference_docname"
		],
		limit=limit,
		order_by="creation desc"
	)
	for task in tasks:
		activities.append({
			"name": task.name,
			"activity_type": "task",
			"creation": task.creation,
			"owner": user,
			"title": task.title,
			"description": task.description,
			"assigned_to": task.assigned_to,
			"status": task.status,
			"reference_doctype": task.reference_doctype or "CRM Lead",
			"reference_docname": task.reference_docname
		})

	# 8. Fetch files/attachments
	attachments = frappe.db.get_all(
		"File",
		filters={"owner": user, "attached_to_doctype": ["in", ["CRM Lead", "CRM Deal", "Contact", "CRM Organization", "CRM Call Log"]]},
		fields=["name", "file_name", "file_type", "file_url", "file_size", "creation", "attached_to_doctype", "attached_to_name"],
		limit=limit,
		order_by="creation desc"
	)
	for file in attachments:
		ref_doctype = file.attached_to_doctype
		ref_docname = file.attached_to_name
		if ref_doctype == "CRM Call Log":
			call_log = frappe.db.get_values("CRM Call Log", ref_docname, ["reference_doctype", "reference_docname"])
			if call_log and call_log[0][0] and call_log[0][1]:
				ref_doctype = call_log[0][0]
				ref_docname = call_log[0][1]
			else:
				links = frappe.db.get_all("Dynamic Link", filters={"parent": ref_docname, "parenttype": "CRM Call Log"}, fields=["link_doctype", "link_name"])
				resolved = False
				for link in links:
					if link.link_doctype in ["CRM Lead", "CRM Deal", "Contact", "CRM Organization"]:
						ref_doctype = link.link_doctype
						ref_docname = link.link_name
						resolved = True
						break
				if not resolved:
					ref_doctype = "CRM Lead"

		activities.append({
			"name": file.name,
			"activity_type": "attachment_log",
			"creation": file.creation,
			"owner": user,
			"data": {
				"type": "Attachment",
				"file_name": file.file_name,
				"file_url": file.file_url,
				"is_private": False
			},
			"reference_doctype": ref_doctype,
			"reference_docname": ref_docname
		})

	activities.sort(key=lambda x: x["creation"], reverse=True)
	return activities[:limit]


@frappe.whitelist()
def get_user_activity_summary(
	user: str, period: str | None = None, from_date: str | None = None, to_date: str | None = None
):
	roles = frappe.get_roles()
	if "System Manager" not in roles and "Sales Manager" not in roles and frappe.session.user != user:
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	now = frappe.utils.nowdate()
	if period == "Today":
		from_date = now
		to_date = now
	elif period == "Last 7 Days":
		from_date = frappe.utils.add_days(now, -6)
		to_date = now
	elif period == "Last 30 Days":
		from_date = frappe.utils.add_days(now, -29)
		to_date = now
	elif period == "This Month":
		from_date = frappe.utils.get_first_day(now)
		to_date = frappe.utils.get_last_day(now)

	date_filter_expr = {}
	if from_date and to_date:
		date_filter_expr = {"creation": ["between", [f"{from_date} 00:00:00", f"{to_date} 23:59:59"]]}
	elif from_date:
		date_filter_expr = {"creation": [">=", f"{from_date} 00:00:00"]}
	elif to_date:
		date_filter_expr = {"creation": ["<=", f"{to_date} 23:59:59"]}

	# 1. Call Analytics
	call_filters = {}
	call_filters.update(date_filter_expr)
	calls = frappe.db.get_all(
		"CRM Call Log",
		or_filters={"owner": user, "caller": user, "receiver": user},
		filters=call_filters,
		fields=["status", "type", "duration"],
	)

	total_calls = len(calls)
	inbound_calls = 0
	outbound_calls = 0
	completed_calls = 0
	busy_calls = 0
	declined_calls = 0
	no_answer_calls = 0
	total_duration = 0

	for c in calls:
		if c.type == "Incoming":
			inbound_calls += 1
		else:
			outbound_calls += 1

		status = (c.status or "").strip().lower()
		if status in ["completed", "in progress", "answered"]:
			completed_calls += 1
			total_duration += c.duration or 0
		elif status == "busy":
			busy_calls += 1
		elif status in ["no answer", "missed"]:
			no_answer_calls += 1
		elif status in ["failed", "canceled", "declined"]:
			declined_calls += 1
		else:
			if status not in ["ringing", "queued", "initiated"]:
				declined_calls += 1

	avg_duration = round(total_duration / completed_calls, 1) if completed_calls > 0 else 0

	# 2. Lead Pipeline & Conversions
	# Check lead conversions and status changes in period
	version_filters = {"owner": user, "ref_doctype": "CRM Lead"}
	version_filters.update(date_filter_expr)
	versions = frappe.db.get_all("Version", filters=version_filters, fields=["docname", "data"])
	status_changes_count = 0
	converted_count = 0
	modified_lead_names = set()
	for v in versions:
		try:
			data = json.loads(v.data)
			if data.get("changed"):
				for change in data["changed"]:
					if change[0] == "status":
						status_changes_count += 1
						modified_lead_names.add(v.docname)
						if change[2] and "converted" in str(change[2]).lower():
							converted_count += 1
		except Exception:
			pass

	created_filters = {"owner": user}
	created_filters.update(date_filter_expr)
	created_leads = frappe.db.get_all("CRM Lead", filters=created_filters, pluck="name")

	assigned_leads = frappe.db.get_all(
		"CRM Lead",
		or_filters={"lead_owner": user, "_assign": ["like", f"%{user}%"]},
		filters=date_filter_expr,
		pluck="name"
	)

	active_lead_names = modified_lead_names | set(created_leads) | set(assigned_leads)

	if active_lead_names:
		lead_status_counts = frappe.db.get_all(
			"CRM Lead",
			filters=[["name", "in", list(active_lead_names)]],
			fields=["status", "count(*) as count"],
			group_by="status",
		)
	else:
		lead_status_counts = []
	total_leads = sum(l.count for l in lead_status_counts)

	# 3. Deals Analytics
	# Check deal status changes and won status in period
	won_statuses = frappe.db.get_all("CRM Deal Status", filters={"type": "Won"}, pluck="name")
	deal_version_filters = {"owner": user, "ref_doctype": "CRM Deal"}
	deal_version_filters.update(date_filter_expr)
	deal_versions = frappe.db.get_all("Version", filters=deal_version_filters, fields=["docname", "data"])
	deal_status_changes_count = 0
	deal_won_count = 0
	modified_deal_names = set()
	for v in deal_versions:
		try:
			data = json.loads(v.data)
			if data.get("changed"):
				for change in data["changed"]:
					if change[0] == "status":
						deal_status_changes_count += 1
						modified_deal_names.add(v.docname)
						if change[2] and change[2] in won_statuses:
							deal_won_count += 1
		except Exception:
			pass

	deal_created_filters = {"owner": user}
	deal_created_filters.update(date_filter_expr)
	created_deals = frappe.db.get_all("CRM Deal", filters=deal_created_filters, pluck="name")

	assigned_deals = frappe.db.get_all(
		"CRM Deal",
		or_filters={"deal_owner": user, "_assign": ["like", f"%{user}%"]},
		filters=date_filter_expr,
		pluck="name"
	)

	active_deal_names = modified_deal_names | set(created_deals) | set(assigned_deals)

	if active_deal_names:
		deal_status_counts = frappe.db.get_all(
			"CRM Deal",
			filters=[["name", "in", list(active_deal_names)]],
			fields=["status", "count(*) as count", "sum(annual_revenue) as total_value"],
			group_by="status",
		)
	else:
		deal_status_counts = []
	total_deals = sum(d.count for d in deal_status_counts)
	total_deal_value = sum((d.total_value or 0) for d in deal_status_counts)

	# 4. Activity Counts for period
	note_filters = {"owner": user}
	note_filters.update(date_filter_expr)
	notes_count = frappe.db.count("FCRM Note", filters=note_filters)

	task_filters = {}
	task_filters.update(date_filter_expr)
	tasks = frappe.db.get_all(
		"CRM Task",
		or_filters={"owner": user, "assigned_to": user},
		filters=task_filters,
		fields=["status"],
	)
	tasks_count = len(tasks)
	tasks_completed = sum(1 for t in tasks if (t.status or "").lower() in ["completed", "closed", "done"])
	tasks_open = tasks_count - tasks_completed

	comm_filters = {}
	comm_filters.update(date_filter_expr)
	emails_count = len(
		frappe.db.get_all(
			"Communication",
			or_filters={"sender": user, "owner": user},
			filters=comm_filters,
			fields=["name"],
		)
	)

	whatsapp_count = 0
	if frappe.db.exists("DocType", "WhatsApp Message"):
		wa_filters = {"owner": user}
		wa_filters.update(date_filter_expr)
		whatsapp_count = frappe.db.count("WhatsApp Message", filters=wa_filters)

	comment_filters = {
		"owner": user,
		"comment_type": "Comment",
		"reference_doctype": ["in", ["CRM Lead", "CRM Deal", "Contact", "CRM Organization", "CRM Call Log"]],
	}
	comment_filters.update(date_filter_expr)
	comments_count = frappe.db.count("Comment", filters=comment_filters)

	edit_filters = {
		"owner": user,
		"ref_doctype": ["in", ["CRM Lead", "CRM Deal", "Contact", "CRM Organization"]],
	}
	edit_filters.update(date_filter_expr)
	edits_count = frappe.db.count("Version", filters=edit_filters)

	total_activities = (
		total_calls + notes_count + tasks_completed + emails_count + whatsapp_count + comments_count + edits_count
	)

	return {
		"calls": {
			"total": total_calls,
			"inbound": inbound_calls,
			"outbound": outbound_calls,
			"completed": completed_calls,
			"busy": busy_calls,
			"declined": declined_calls,
			"no_answer": no_answer_calls,
			"duration": total_duration,
			"avg_duration": avg_duration,
		},
		"leads": {
			"total": total_leads,
			"by_status": lead_status_counts,
			"status_changes": status_changes_count,
			"converted": converted_count,
		},
		"deals": {
			"total": total_deals,
			"total_value": total_deal_value,
			"by_status": deal_status_counts,
			"status_changes": deal_status_changes_count,
			"won": deal_won_count,
		},
		"activities": {
			"total": total_activities,
			"notes": notes_count,
			"tasks_total": tasks_count,
			"tasks_completed": tasks_completed,
			"tasks_open": tasks_open,
			"emails": emails_count,
			"whatsapp": whatsapp_count,
			"comments": comments_count,
			"edits": edits_count,
		},
	}



