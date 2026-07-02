import frappe
from frappe import _
from werkzeug.wrappers import Response
from crm.integrations.api import get_contact_by_phone_number


@frappe.whitelist()
def is_enabled():
	return frappe.db.get_single_value("CRM Vobiz Settings", "enabled")


@frappe.whitelist()
def get_vobiz_credentials():
	user = frappe.session.user
	user_keys = [user]
	email = frappe.db.get_value("User", user, "email")
	if email:
		user_keys.append(email)

	agent_name = None
	for k in user_keys:
		if frappe.db.exists("CRM Telephony Agent", k):
			agent_name = k
			break

	if not agent_name:
		return {}
	agent = frappe.get_doc("CRM Telephony Agent", agent_name)
	vobiz_settings = frappe.get_single("CRM Vobiz Settings")
	return {
		"username": agent.vobiz_username,
		"password": agent.get_password("vobiz_password") if agent.vobiz_password else "",
		"number": agent.vobiz_number,
		"appId": vobiz_settings.app_id,
		"appSecret": vobiz_settings.get_password("api_password") if vobiz_settings.api_password else "",
		"websocketUrlOverride": vobiz_settings.websocket_url_override,
		"record_calls": bool(vobiz_settings.record_calls),
	}


@frappe.whitelist(allow_guest=True)
def voice(**kwargs):
	"""Webhook called by Vobiz to get instructions for call handling (Answer URL)."""
	try:
		with open("/workspace/scratch_webhook.log", "a") as f:
			f.write(f"Voice webhook called: {frappe.as_json(kwargs)}\n")
	except Exception as e:
		pass
	frappe.log_error(title="Vobiz Voice Webhook", message=frappe.as_json(kwargs))
	args = frappe._dict(kwargs)
	vobiz_settings = frappe.get_single("CRM Vobiz Settings")
	enabled = vobiz_settings.enabled
	if not enabled:
		return Response("<Response><Hangup/></Response>", mimetype="text/xml")
	
	record_calls = vobiz_settings.record_calls
	record_attr = ' record="true"' if record_calls else ""

	raw_from = args.get("From") or args.get("from") or ""
	raw_to = args.get("To") or args.get("to") or ""
	route_type = (args.get("RouteType") or args.get("routetype") or "").lower()
	call_sid = args.get("CallUUID") or args.get("calluuid") or args.get("CallSid") or args.get("callsid") or frappe.generate_hash(length=12)

	# Clean numbers
	vobiz_username = raw_from.replace("sip:", "").split("@")[0]
	agent = frappe.db.get_value("CRM Telephony Agent", {"vobiz_username": vobiz_username}, ["name", "vobiz_number"], as_dict=True)

	is_sdk_call = raw_from.startswith("sip:") or route_type == "sip" or bool(agent)

	if is_sdk_call:
		# Browser SDK outbound call: From is sip:username@domain, To is dialed phone number
		caller_id = agent.vobiz_number if agent else raw_to
		destination = raw_to

		# Ensure destination starts with +
		if destination and not destination.startswith("+"):
			destination = f"+{destination}"

		# Create Outgoing Call Log
		create_call_log(
			call_id=call_sid,
			from_number=caller_id,
			to_number=destination,
			call_type="Outgoing",
			agent=agent.name if agent else frappe.session.user,
		)

		xml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Dial callerId="{caller_id}"{record_attr}>
        <Number>{destination}</Number>
    </Dial>
</Response>"""
		return Response(xml_response, mimetype="text/xml")

	else:
		# Inbound call: From is caller phone number, To is Vobiz number
		destination_number = raw_to
		caller_number = raw_from
		if caller_number and not caller_number.startswith("+"):
			caller_number = f"+{caller_number}"

		# Find the agent owning this Vobiz number
		agent = frappe.db.get_value(
			"CRM Telephony Agent",
			{"vobiz_number": destination_number},
			["name", "vobiz_username", "call_receiving_device", "mobile_no"],
			as_dict=True,
		)

		if not agent:
			# Fallback: find any agent if no exact number matches
			agents = frappe.get_all("CRM Telephony Agent", filters={"default_medium": "Vobiz"}, fields=["name", "vobiz_username", "call_receiving_device", "mobile_no"])
			agent = agents[0] if agents else None

		if not agent or not agent.vobiz_username:
			xml_response = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Speak>We are sorry, but no agent is currently available to take your call. Goodbye.</Speak>
    <Hangup/>
</Response>"""
			return Response(xml_response, mimetype="text/xml")

		# Create Inbound Call Log
		create_call_log(
			call_id=call_sid,
			from_number=caller_number,
			to_number=destination_number,
			call_type="Incoming",
			agent=agent.name,
		)

		sip_domain = "sip.vobiz.ai"

		# Route to device (Computer or Phone)
		if agent.call_receiving_device == "Phone" and agent.mobile_no:
			xml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Dial callerId="{destination_number}" timeout="30"{record_attr}>
        <Number>{agent.mobile_no}</Number>
    </Dial>
</Response>"""
		else:
			# Ring browser client via WebRTC SIP endpoint
			xml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Dial callerId="{caller_number}" timeout="30"{record_attr}>
        <User>sip:{agent.vobiz_username}@{sip_domain}</User>
    </Dial>
    <Speak>The user is currently on another call. Please try again later. Goodbye.</Speak>
    <Hangup/>
</Response>"""

		return Response(xml_response, mimetype="text/xml")


@frappe.whitelist()
def update_vobiz_call_status(call_sid: str, status: str, duration: int = 0):
	"""Allows the WebRTC frontend client to update the call log status directly."""
	call_log_name = None

	# 1. Direct lookup by document name
	if call_sid and frappe.db.exists("CRM Call Log", call_sid):
		call_log_name = call_sid
	elif call_sid:
		# 2. Fallback: lookup by 'id' field (autoname source)
		call_log_name = frappe.db.get_value("CRM Call Log", {"id": call_sid}, "name")

	if not call_log_name:
		# 3. Last resort: find most recent active Vobiz call for this user
		CallLog = frappe.qb.DocType("CRM Call Log")
		result = (
			frappe.qb.from_(CallLog)
			.select(CallLog.name)
			.where(CallLog.telephony_medium == "Vobiz")
			.where(CallLog.status.isin(["Initiated", "Ringing", "In Progress"]))
			.where((CallLog.caller == frappe.session.user) | (CallLog.receiver == frappe.session.user))
			.orderby(CallLog.creation, order=frappe.qb.desc)
			.limit(1)
			.run(as_dict=True)
		)
		if result:
			call_log_name = result[0].name

	if not call_log_name:
		return {"ok": False, "error": "Call log not found"}

	call_log = frappe.get_doc("CRM Call Log", call_log_name)
	call_log.status = status
	if duration:
		call_log.duration = duration
	if frappe.session.user and frappe.session.user != "Guest":
		if call_log.type == "Incoming":
			call_log.receiver = frappe.session.user
		else:
			call_log.caller = frappe.session.user
	call_log.save(ignore_permissions=True)
	frappe.db.commit()

	# Publish socket event to update other client instances
	frappe.publish_realtime("vobiz_call_update", {
		"CallSid": call_log_name,
		"Status": status,
		"Duration": duration
	})

	# Enqueue telephony call log sync in the background
	frappe.enqueue("crm.integrations.vobiz.sync.sync_telephony_call_logs", queue="short")

	return {"ok": True}


def create_call_log(call_id, from_number, to_number, call_type, agent, status="Initiated"):
	call_log = frappe.new_doc("CRM Call Log")
	call_log.id = call_id
	call_log.to = to_number
	call_log.status = status
	call_log.type = call_type
	call_log.telephony_medium = "Vobiz"
	setattr(call_log, "from", from_number)

	if call_type == "Incoming":
		call_log.receiver = agent
	else:
		call_log.caller = agent

	# Link call log with lead/deal based on caller number / destination number
	contact_number = from_number if call_type == "Incoming" else to_number
	link_call_log_to_contact(contact_number, call_log)

	call_log.save(ignore_permissions=True)
	frappe.db.commit()

	# Broadcast realtime event
	frappe.publish_realtime("vobiz_call", {
		"CallSid": call_id,
		"From": from_number,
		"To": to_number,
		"Direction": "inbound" if call_type == "Incoming" else "outbound-api",
		"Status": status.lower(),
		"AgentEmail": agent
	})

	return call_log


def link_call_log_to_contact(contact_number, call_log):
	contact = get_contact_by_phone_number(contact_number)
	if contact.get("name"):
		doctype = "Contact"
		docname = contact.get("name")
		if contact.get("lead"):
			doctype = "CRM Lead"
			docname = contact.get("lead")
		elif contact.get("deal"):
			doctype = "CRM Deal"
			docname = contact.get("deal")
		call_log.link_with_reference_doc(doctype, docname)


@frappe.whitelist(allow_guest=True)
def hangup(**kwargs):
	"""Webhook called by Vobiz when a call is hung up."""
	args = frappe._dict(kwargs)
	enabled = frappe.db.get_single_value("CRM Vobiz Settings", "enabled")
	if not enabled:
		return Response("OK", status=200)

	call_sid = args.get("CallUUID") or args.get("calluuid") or args.get("CallSid") or args.get("callsid")
	try:
		with open("/workspace/scratch_webhook.log", "a") as f:
			f.write(f"Hangup webhook called: {frappe.as_json(kwargs)}\n")
	except Exception:
		pass
	if not call_sid:
		return Response("OK", status=200)

	# Find call log name by document name or by id field
	call_log_name = None
	if frappe.db.exists("CRM Call Log", call_sid):
		call_log_name = call_sid
	else:
		call_log_name = frappe.db.get_value("CRM Call Log", {"id": call_sid}, "name")

	if not call_log_name:
		return Response("OK", status=200)

	call_log = frappe.get_doc("CRM Call Log", call_log_name)

	# Map status
	vobiz_status = (args.get("Status") or args.get("status") or "").lower()
	status_map = {
		"completed": "Completed",
		"busy": "Busy",
		"failed": "Failed",
		"no-answer": "No Answer",
		"canceled": "Canceled"
	}
	
	if call_log.status in ["Completed", "Busy", "No Answer", "Canceled"]:
		new_status = call_log.status
	else:
		new_status = status_map.get(vobiz_status, call_log.status or "Completed")
	call_log.status = new_status

	duration = args.get("Duration") or args.get("duration") or 0
	try:
		call_log.duration = int(duration)
	except ValueError:
		pass

	start_time = args.get("StartTime") or args.get("starttime")
	end_time = args.get("EndTime") or args.get("endtime")

	if start_time:
		try:
			call_log.start_time = frappe.utils.to_datetime(start_time)
		except Exception:
			pass

	if end_time:
		try:
			call_log.end_time = frappe.utils.to_datetime(end_time)
		except Exception:
			pass

	# Capture recording URL from Vobiz hangup payload (if present)
	recording_url = args.get("RecordUrl") or args.get("RecordingUrl") or args.get("recordurl") or args.get("recording_url") or ""
	if recording_url:
		call_log.recording_url = recording_url

	call_log.save(ignore_permissions=True)
	frappe.db.commit()

	# Publish socket event to update clients
	frappe.publish_realtime("vobiz_call_update", {
		"CallSid": call_log_name,
		"Status": new_status,
		"Duration": call_log.duration,
		"RecordingUrl": recording_url or ""
	})

	# Enqueue telephony call log sync in the background
	frappe.enqueue("crm.integrations.vobiz.sync.sync_telephony_call_logs", queue="short")

	# If recording is enabled but not yet captured, fetch it from Vobiz API after a delay
	if not recording_url and frappe.db.get_single_value("CRM Vobiz Settings", "record_calls"):
		frappe.enqueue(
			"crm.integrations.vobiz.api.fetch_vobiz_recording",
			queue="short",
			call_uuid=call_sid,
			call_log_name=call_log_name,
			at_front=False,
			enqueue_after_commit=True,
		)

	return Response("OK", status=200)


def fetch_vobiz_recording(call_uuid, call_log_name, retry_count=0):
	"""Fetch recording URL from Vobiz REST API and update the CRM Call Log."""
	import requests
	import time

	max_retries = 5
	if retry_count >= max_retries:
		frappe.log_error(
			title="Vobiz Recording Fetch Failed",
			message=f"Could not fetch recording for call {call_uuid} after {max_retries} retries"
		)
		return

	vobiz_settings = frappe.get_single("CRM Vobiz Settings")
	auth_id = vobiz_settings.auth_id
	auth_token = vobiz_settings.get_password("api_password") if vobiz_settings.api_password else ""

	if not auth_id or not auth_token:
		return

	# Wait a bit for Vobiz to process the recording (increases with each retry)
	time.sleep(5 + (retry_count * 5))

	try:
		# Query Vobiz Recording API for this call
		api_url = f"https://api.vobiz.ai/api/v1/Account/{auth_id}/Recording/"
		response = requests.get(
			api_url,
			params={"call_uuid": call_uuid},
			headers={
				"X-Auth-ID": auth_id,
				"X-Auth-Token": auth_token,
			},
			timeout=10,
		)

		if response.status_code == 200:
			data = response.json()
			recordings = data.get("objects") or data.get("recordings") or data.get("results") or []

			# Also check if the response itself is a list
			if isinstance(data, list):
				recordings = data

			recording_url = None
			for rec in recordings:
				url = rec.get("recording_url") or rec.get("RecordUrl") or rec.get("record_url") or rec.get("url") or ""
				if url:
					recording_url = url
					break

			if recording_url:
				call_log = frappe.get_doc("CRM Call Log", call_log_name)
				if not call_log.recording_url:
					call_log.recording_url = recording_url
					call_log.save(ignore_permissions=True)
					frappe.db.commit()
				return

		# If no recording found yet, retry after a delay
		frappe.enqueue(
			"crm.integrations.vobiz.api.fetch_vobiz_recording",
			queue="short",
			call_uuid=call_uuid,
			call_log_name=call_log_name,
			retry_count=retry_count + 1,
		)

	except Exception as e:
		frappe.log_error(
			title="Vobiz Recording API Error",
			message=f"Error fetching recording for {call_uuid}: {str(e)}"
		)
		# Retry on error
		frappe.enqueue(
			"crm.integrations.vobiz.api.fetch_vobiz_recording",
			queue="short",
			call_uuid=call_uuid,
			call_log_name=call_log_name,
			retry_count=retry_count + 1,
		)


@frappe.whitelist()
def test_recording_api():
	"""Temporary debug function to print Vobiz recordings."""
	import requests
	import json
	vobiz_settings = frappe.get_single("CRM Vobiz Settings")
	auth_id = vobiz_settings.auth_id
	auth_token = vobiz_settings.get_password("api_password") if vobiz_settings.api_password else ""
	api_url = f"https://api.vobiz.ai/api/v1/Account/{auth_id}/Recording/"
	
	print(f"Auth ID: {auth_id}")
	try:
		response = requests.get(
			api_url,
			headers={
				"X-Auth-ID": auth_id,
				"X-Auth-Token": auth_token,
			},
			timeout=10,
		)
		print(f"Status Code: {response.status_code}")
		print(f"Response: {response.text}")
	except Exception as e:
		print(f"Error: {str(e)}")


@frappe.whitelist(allow_guest=True)
def upload_recording(call_sid):
	"""Handles recording uploads from the browser WebRTC client."""
	if not call_sid:
		return {"ok": False, "error": "Missing Call SID"}

	# Find the call log by name or id field
	call_log_name = None
	if frappe.db.exists("CRM Call Log", call_sid):
		call_log_name = call_sid
	else:
		call_log_name = frappe.db.get_value("CRM Call Log", {"id": call_sid}, "name")

	if not call_log_name:
		return {"ok": False, "error": "Call log not found"}

	# Get the file from request
	file = frappe.request.files.get("file")
	if not file:
		return {"ok": False, "error": "No file uploaded"}

	from frappe.utils.file_manager import save_file

	# Save the file to Frappe's file system
	saved_file = save_file(
		fname=f"call_recording_{call_sid}.webm",
		content=file.read(),
		dt="CRM Call Log",
		dn=call_log_name,
		is_private=0
	)

	# Update CRM Call Log
	call_log = frappe.get_doc("CRM Call Log", call_log_name)
	call_log.recording_url = saved_file.file_url
	call_log.status = "Completed"
	if frappe.session.user and frappe.session.user != "Guest":
		if call_log.type == "Incoming":
			call_log.receiver = frappe.session.user
		else:
			call_log.caller = frappe.session.user
	call_log.save(ignore_permissions=True)
	frappe.db.commit()

	# Publish socket event so frontend knows the recording has been uploaded
	frappe.publish_realtime("vobiz_call_update", {
		"CallSid": call_log_name,
		"Status": call_log.status,
		"Duration": call_log.duration,
		"recording_url": saved_file.file_url
	})

	return {"ok": True, "recording_url": saved_file.file_url}



