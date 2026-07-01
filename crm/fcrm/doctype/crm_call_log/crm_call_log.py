# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _, generate_hash
from frappe.model.document import Document

from crm.integrations.api import get_contact_by_phone_number
from crm.utils import seconds_to_duration


class CRMCallLog(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.core.doctype.dynamic_link.dynamic_link import DynamicLink
		from frappe.types import DF

		caller: DF.Link | None
		duration: DF.Duration | None
		end_time: DF.Datetime | None
		id: DF.Data | None
		links: DF.Table[DynamicLink]
		medium: DF.Data | None
		note: DF.Link | None
		receiver: DF.Link | None
		recording_url: DF.SmallText | None
		reference_docname: DF.DynamicLink | None
		reference_doctype: DF.Link | None
		start_time: DF.Datetime | None
		status: DF.Literal[
			"Initiated",
			"Ringing",
			"In Progress",
			"Completed",
			"Failed",
			"Busy",
			"No Answer",
			"Queued",
			"Canceled",
		]
		telephony_medium: DF.Literal["", "Manual", "Twilio", "Exotel", "Vobiz"]
		to: DF.Data
		type: DF.Literal["Incoming", "Outgoing"]
	# end: auto-generated types

	def before_insert(self):
		if not self.id:
			self.id = generate_hash(length=12)
		if not self.telephony_medium:
			self.telephony_medium = "Manual"

	def before_save(self):
		self.update_lead_details()

	def update_lead_details(self):
		lead_name = self.get_linked_lead_name()
		if lead_name:
			lead = frappe.get_cached_doc("CRM Lead", lead_name)
			self.lead_name = lead.lead_name
			self.organization = lead.organization
			self.mobile_no = lead.mobile_no
			self.call_flag = getattr(lead, "call_flag", None)
		else:
			self.lead_name = None
			self.organization = None
			self.mobile_no = None
			self.call_flag = None

		self.direction = "inbound" if self.type == "Incoming" else "outbound"
		
		if self.start_time:
			import pytz
			dt = frappe.utils.to_datetime(self.start_time)
			if dt:
				if dt.tzinfo is None:
					dt = pytz.utc.localize(dt)
				system_tz = pytz.timezone(frappe.utils.get_system_timezone())
				local_dt = dt.astimezone(system_tz)
				self.call_date = local_dt.strftime("%Y-%m-%d")
				self.call_time = local_dt.strftime("%H:%M:%S")

	@staticmethod
	def default_list_data():
		columns = [
			{
				"label": "Caller",
				"type": "Link",
				"key": "caller",
				"options": "User",
				"width": "9rem",
			},
			{
				"label": "Receiver",
				"type": "Link",
				"key": "receiver",
				"options": "User",
				"width": "9rem",
			},
			{
				"label": "Type",
				"type": "Select",
				"key": "type",
				"width": "9rem",
			},
			{
				"label": "Status",
				"type": "Select",
				"key": "status",
				"width": "9rem",
			},
			{
				"label": "Duration",
				"type": "Duration",
				"key": "duration",
				"width": "6rem",
			},
			{
				"label": "From (number)",
				"type": "Data",
				"key": "from",
				"width": "9rem",
			},
			{
				"label": "To (number)",
				"type": "Data",
				"key": "to",
				"width": "9rem",
			},
			{
				"label": "Created On",
				"type": "Datetime",
				"key": "creation",
				"width": "8rem",
			},
		]
		rows = [
			"name",
			"caller",
			"receiver",
			"type",
			"status",
			"duration",
			"from",
			"to",
			"note",
			"recording_url",
			"reference_doctype",
			"reference_docname",
			"creation",
		]
		return {"columns": columns, "rows": rows}

	def parse_list_data(calls):
		return [parse_call_log(call) for call in calls] if calls else []

	def has_link(self, doctype, name):
		for link in self.links:
			if link.link_doctype == doctype and link.link_name == name:
				return True

	def link_with_reference_doc(self, reference_doctype, reference_name):
		if self.has_link(reference_doctype, reference_name):
			return

		self.append("links", {"link_doctype": reference_doctype, "link_name": reference_name})

	def as_dict(self, *args, **kwargs):
		d = super().as_dict(*args, **kwargs)
		if d.get("recording_url"):
			d["recording_url_path"] = (
				f"/api/method/crm.integrations.api.get_recording_url?call_log_name={d.get('name')}"
			)
		return d

	def on_update(self):
		self.update_linked_lead()

	def after_insert(self):
		self.update_linked_lead()

	def update_linked_lead(self):
		lead_name = self.get_linked_lead_name()
		if lead_name and frappe.db.exists("CRM Lead", lead_name):
			# Map Direction: set to inbound if this lead has ANY incoming call log
			has_inbound = False
			if self.type == "Incoming":
				has_inbound = True
			else:
				has_inbound = frappe.db.sql(
					"""
					select cl.name
					from `tabCRM Call Log` cl
					left join `tabDynamic Link` dl on dl.parent = cl.name and dl.parenttype = 'CRM Call Log'
					where cl.type = 'Incoming'
					  and cl.name != %s
					  and (
					    (cl.reference_doctype = 'CRM Lead' and cl.reference_docname = %s)
					    or (dl.link_doctype = 'CRM Lead' and dl.link_name = %s)
					  )
					limit 1
					""",
					(self.name, lead_name, lead_name),
				)
			
			lead = frappe.get_doc("CRM Lead", lead_name)
			new_direction = "inbound" if has_inbound else "outbound"
			direction_changed = lead.direction != new_direction
			if direction_changed:
				lead.direction = new_direction

			# Do not overwrite lead details with older call logs
			more_recent_exists = False
			if self.start_time:
				more_recent_exists = frappe.db.sql(
					"""
					select cl.name
					from `tabCRM Call Log` cl
					left join `tabDynamic Link` dl on dl.parent = cl.name and dl.parenttype = 'CRM Call Log'
					where cl.start_time > %s
					  and cl.name != %s
					  and (
					    (cl.reference_doctype = 'CRM Lead' and cl.reference_docname = %s)
					    or (dl.link_doctype = 'CRM Lead' and dl.link_name = %s)
					  )
					limit 1
					""",
					(self.start_time, self.name, lead_name, lead_name),
				)
				
			if not more_recent_exists:
				# Map Date and Time
				if self.start_time:
					import pytz
					dt = frappe.utils.to_datetime(self.start_time)
					if dt:
						if dt.tzinfo is None:
							dt = pytz.utc.localize(dt)
						system_tz = pytz.timezone(frappe.utils.get_system_timezone())
						local_dt = dt.astimezone(system_tz)
						lead.call_date = local_dt.strftime("%Y-%m-%d")
						lead.call_time = local_dt.strftime("%H:%M:%S")
						
				# Map Duration
				if self.duration is not None:
					lead.call_duration = int(self.duration)
				
			if direction_changed or not more_recent_exists:
				# Save Lead
				lead.save(ignore_permissions=True, ignore_version=True)

	def get_linked_lead_name(self):
		if self.reference_doctype == "CRM Lead" and self.reference_docname:
			return self.reference_docname
		
		# If linked to a CRM Deal, resolve to its lead
		if self.reference_doctype == "CRM Deal" and self.reference_docname:
			lead_name = frappe.db.get_value("CRM Deal", self.reference_docname, "lead")
			if lead_name:
				return lead_name
				
		for link in getattr(self, "links", []):
			if link.link_doctype == "CRM Lead" and link.link_name:
				return link.link_name
			if link.link_doctype == "CRM Deal" and link.link_name:
				lead_name = frappe.db.get_value("CRM Deal", link.link_name, "lead")
				if lead_name:
					return lead_name

		# Fallback: search by phone number of the call log
		phone = self.to if self.type == "Outgoing" else self.get("from")
		if phone:
			cleaned_phone = (phone or "").replace("+", "").replace("-", "").replace(" ", "").replace("(", "").replace(")", "")
			if cleaned_phone and len(cleaned_phone) >= 5:
				lead_name = frappe.db.get_value(
					"CRM Lead",
					{"mobile_no": ["like", f"%{cleaned_phone}%"], "converted": 0},
					"name",
					order_by="modified desc"
				)
				if lead_name:
					return lead_name
		return None



def parse_call_log(call):
	call["show_recording"] = False
	call["_duration"] = seconds_to_duration(call.get("duration"))
	if call.get("type") == "Incoming":
		call["activity_type"] = "incoming_call"
		contact = get_contact_by_phone_number(call.get("from"))
		receiver = (
			frappe.db.get_values("User", call.get("receiver"), ["full_name", "user_image"])[0]
			if call.get("receiver")
			else [None, None]
		)
		call["_caller"] = {
			"label": contact.get("full_name", "Unknown"),
			"image": contact.get("image"),
		}
		call["_receiver"] = {
			"label": receiver[0],
			"image": receiver[1],
		}
	elif call.get("type") == "Outgoing":
		call["activity_type"] = "outgoing_call"
		contact = get_contact_by_phone_number(call.get("to"))
		caller = (
			frappe.db.get_values("User", call.get("caller"), ["full_name", "user_image"])[0]
			if call.get("caller")
			else [None, None]
		)
		call["_caller"] = {
			"label": caller[0],
			"image": caller[1],
		}
		call["_receiver"] = {
			"label": contact.get("full_name", "Unknown"),
			"image": contact.get("image"),
		}

	return call


@frappe.whitelist()
def get_call_log(name: str):
	call = frappe.get_cached_doc(
		"CRM Call Log",
		name,
		fields=[
			"name",
			"caller",
			"receiver",
			"duration",
			"type",
			"status",
			"from",
			"to",
			"note",
			"recording_url",
			"recording_url_path",
			"reference_doctype",
			"reference_docname",
			"creation",
		],
	).as_dict()

	call = parse_call_log(call)

	notes = []
	tasks = []

	if call.get("note"):
		note = frappe.get_cached_doc("FCRM Note", call.get("note")).as_dict()
		notes.append(note)

	if call.get("reference_doctype") and call.get("reference_docname"):
		if call.get("reference_doctype") == "CRM Lead":
			call["_lead"] = call.get("reference_docname")
		elif call.get("reference_doctype") == "CRM Deal":
			call["_deal"] = call.get("reference_docname")

	if call.get("links"):
		for link in call.get("links"):
			if link.get("link_doctype") == "CRM Task":
				task = frappe.get_cached_doc("CRM Task", link.get("link_name")).as_dict()
				tasks.append(task)
			elif link.get("link_doctype") == "FCRM Note":
				note = frappe.get_cached_doc("FCRM Note", link.get("link_name")).as_dict()
				notes.append(note)
			elif link.get("link_doctype") == "CRM Lead":
				call["_lead"] = link.get("link_name")
			elif link.get("link_doctype") == "CRM Deal":
				call["_deal"] = link.get("link_name")

	call["_tasks"] = tasks
	call["_notes"] = notes
	return call


@frappe.whitelist()
def create_lead_from_call_log(call_log: str | dict, lead_details: str | dict | None = None):
	call_log_data = frappe.parse_json(call_log or {})

	if isinstance(call_log_data, str):
		call_log_name = call_log_data
	elif isinstance(call_log_data, dict):
		call_log_name = call_log_data.get("name")
	else:
		call_log_name = None

	if not call_log_name:
		frappe.throw(_("A valid call log is required."), frappe.ValidationError)

	call_doc = frappe.get_doc("CRM Call Log", call_log_name)

	if not call_doc.has_permission("write"):
		frappe.throw(_("You are not permitted to update this call log."), frappe.PermissionError)

	if not frappe.has_permission("CRM Lead", "create"):
		frappe.throw(_("You are not permitted to create leads."), frappe.PermissionError)

	lead_details_data = frappe.parse_json(lead_details or {})
	if lead_details_data and not isinstance(lead_details_data, dict):
		frappe.throw(_("Invalid lead details supplied."), frappe.ValidationError)

	lead = frappe.new_doc("CRM Lead")
	meta = frappe.get_meta("CRM Lead")
	valid_fieldnames = [df.fieldname for df in meta.fields]

	sanitized_details = {
		key: value for key, value in (lead_details_data or {}).items() if key in valid_fieldnames
	}

	if "lead_owner" in valid_fieldnames and not sanitized_details.get("lead_owner"):
		sanitized_details["lead_owner"] = frappe.session.user

	if "mobile_no" in valid_fieldnames and not sanitized_details.get("mobile_no"):
		sanitized_details["mobile_no"] = call_doc.get("from") or ""

	if "first_name" in valid_fieldnames and not sanitized_details.get("first_name"):
		reference_label = sanitized_details.get("mobile_no") or call_doc.name
		sanitized_details["first_name"] = _("Lead from call {0}").format(reference_label)

	lead.update(sanitized_details)
	lead.insert()

	call_doc.link_with_reference_doc("CRM Lead", lead.name)
	call_doc.save()

	return lead.name
