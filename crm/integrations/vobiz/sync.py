import os
import frappe
from frappe import _
from pymongo import MongoClient

def get_mongo_uri():
	mongo_uri = os.environ.get("MONGO_URI")
	if mongo_uri:
		return mongo_uri
	wsl_ip_path = "/workspace/scratch/wsl_ip.txt"
	if os.path.exists(wsl_ip_path):
		try:
			with open(wsl_ip_path, "r") as f:
				ip = f.read().strip()
				if ip:
					return f"mongodb://{ip}:27018/aiprof_telephony"
		except Exception:
			pass
	return "mongodb://myAdminUser:Hit%40042@172.17.0.1:27017/aiprof_telephony?authSource=admin"


@frappe.whitelist()
def sync_telephony_call_logs():
	mongo_uri = get_mongo_uri()

	try:
		client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
		db = client.get_database("aiprof_telephony")
		# Fetch all call logs, sorted by latest first
		mongo_logs = list(db.CallLogs.find().sort("_id", -1).limit(2500))
	except Exception as e:
		frappe.log_error(title="AIProf MongoDB Connection Error", message=str(e))
		return {"status": "error", "message": f"Failed to connect to MongoDB: {str(e)}"}

	synced_count = 0
	leads_created_count = 0
	updated_leads = set()
	
	for log in mongo_logs:
		try:
			# Use call_id or room_sid or string of _id as the unique ID
			call_id = log.get("call_id") or log.get("room_sid") or str(log.get("_id"))
			if not call_id:
				continue
				
			# Map Direction
			direction = log.get("direction", "outbound")
			call_type = "Outgoing" if direction == "outbound" else "Incoming"
			
			# Map Phone Numbers
			customer_phone = (log.get("caller_identity") or {}).get("phone") or ""
			if customer_phone and not customer_phone.startswith("+"):
				customer_phone = f"+{customer_phone}"
				
			# Default system Vobiz number
			system_number = "+918071580580"
			
			if call_type == "Outgoing":
				from_number = system_number
				to_number = customer_phone
			else:
				from_number = customer_phone
				to_number = system_number
				
			contact_number = to_number if call_type == "Outgoing" else from_number
			
			# Check if Lead/Contact/Deal exists
			from crm.integrations.api import get_contact_by_phone_number
			target_doctype = None
			target_docname = None
			
			if contact_number:
				contact_info = get_contact_by_phone_number(contact_number)
				if contact_info.get("lead"):
					target_doctype = "CRM Lead"
					target_docname = contact_info.get("lead")
				elif contact_info.get("deal"):
					target_doctype = "CRM Deal"
					target_docname = contact_info.get("deal")
				elif contact_info.get("name"):
					target_doctype = "Contact"
					target_docname = contact_info.get("name")
					
			# Check if call log already exists in CRM
			call_log_exists = frappe.db.exists("CRM Call Log", call_id)
			
			# Get/Create Lead and update call properties if not already updated in this run
			lead_doc = None
			is_new_lead = False
			active_lead_name = None
			
			# Only attempt to create/update Lead if the phone number consists of digits
			contact_number_cleaned = (contact_number or "").replace("+", "").replace("-", "").replace(" ", "").replace("(", "").replace(")", "")
			is_valid_phone = contact_number_cleaned.isdigit() and len(contact_number_cleaned) >= 5
			
			if is_valid_phone:
				# Check if there is an active unconverted lead for this phone number
				active_lead_name = frappe.db.get_value(
					"CRM Lead",
					{"mobile_no": ["like", f"%{contact_number_cleaned}%"], "converted": 0},
					"name",
					order_by="modified desc"
				)
				
				if active_lead_name:
					if active_lead_name not in updated_leads:
						lead_doc = frappe.get_doc("CRM Lead", active_lead_name)
				elif target_doctype == "CRM Lead":
					if target_docname not in updated_leads:
						lead_doc = frappe.get_doc("CRM Lead", target_docname)
				elif not target_doctype and contact_number:
					caller_name = (log.get("caller_identity") or {}).get("name") or _("Lead from Telephony")
					lead_doc = frappe.new_doc("CRM Lead")
					lead_doc.first_name = caller_name
					lead_doc.mobile_no = contact_number
					lead_doc.status = "New Lead"
					lead_doc.lead_owner = "Administrator"
					is_new_lead = True
					leads_created_count += 1
	
			if lead_doc:
				# Check if a more recent call log exists in the DB for this lead
				more_recent_exists = False
				start_time_raw = (log.get("timestamps") or {}).get("start")
				if start_time_raw and not is_new_lead:
					start_time_dt = frappe.utils.to_datetime(start_time_raw)
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
						(start_time_dt, call_id, lead_doc.name, lead_doc.name),
					)

				# Map Direction (inbound/outbound): set to inbound if lead has any inbound call log (or this current log is inbound)
				new_direction = "outbound"
				is_curr_inbound = log.get("direction") == "inbound"
				if is_curr_inbound:
					new_direction = "inbound"
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
						(call_id, lead_doc.name, lead_doc.name),
					)
					if has_inbound:
						new_direction = "inbound"
						
				direction_changed = lead_doc.direction != new_direction
				if direction_changed:
					lead_doc.direction = new_direction

				lead_details_updated = False
				if not more_recent_exists:
					# Map Campaign Name to Organization
					campaign_name = (log.get("campaign_info") or {}).get("name")
					if campaign_name and lead_doc.organization != campaign_name:
						lead_doc.organization = campaign_name
						lead_details_updated = True
						
					# Map Date and Time
					if start_time_raw:
						import pytz
						dt = frappe.utils.to_datetime(start_time_raw)
						if dt:
							if dt.tzinfo is None:
								dt = pytz.utc.localize(dt)
							system_tz = pytz.timezone(frappe.utils.get_system_timezone())
							local_dt = dt.astimezone(system_tz)
							call_date_val = local_dt.strftime("%Y-%m-%d")
							call_time_val = local_dt.strftime("%H:%M:%S")
							if lead_doc.call_date != call_date_val or lead_doc.call_time != call_time_val:
								lead_doc.call_date = call_date_val
								lead_doc.call_time = call_time_val
								lead_details_updated = True
							
					# Map Duration
					duration_val = (log.get("timestamps") or {}).get("duration_sec")
					if duration_val is not None:
						duration_val_int = int(duration_val)
						if lead_doc.call_duration != duration_val_int:
							lead_doc.call_duration = duration_val_int
							lead_details_updated = True
						
					# Map Flags
					flag_val = (log.get("analysis") or {}).get("flag")
					if flag_val and lead_doc.call_flag != flag_val:
						lead_doc.call_flag = flag_val
						lead_details_updated = True

				# Save Lead
				if is_new_lead:
					lead_doc.insert(ignore_permissions=True)
					target_doctype = "CRM Lead"
					target_docname = lead_doc.name
				elif direction_changed or lead_details_updated:
					lead_doc.save(ignore_permissions=True)
					
				updated_leads.add(lead_doc.name)
	
			# Create and insert call log if it does not already exist
			if not call_log_exists:
				# Map Status
				mongo_status = (log.get("call_status") or "").lower()
				status_map = {
					"answered": "Completed",
					"no-answer": "No Answer",
					"busy": "Busy",
					"failed": "Failed",
					"completed": "Completed",
					"ringing": "Ringing",
					"canceled": "Canceled"
				}
				status = status_map.get(mongo_status, "Completed")
				
				# Map Timestamps & Duration
				timestamps = log.get("timestamps") or {}
				start_time = timestamps.get("start")
				end_time = timestamps.get("end")
				duration = timestamps.get("duration_sec") or 0
				
				call_log = frappe.new_doc("CRM Call Log")
				call_log.id = call_id
				call_log.status = status
				call_log.type = call_type
				call_log.telephony_medium = "Vobiz"
				call_log.from_number = from_number
				setattr(call_log, "from", from_number)
				call_log.to = to_number
				call_log.duration = int(duration)
				
				if start_time:
					call_log.start_time = frappe.utils.to_datetime(start_time)
				if end_time:
					call_log.end_time = frappe.utils.to_datetime(end_time)
					
				recording_url = log.get("recording_url")
				if recording_url:
					call_log.recording_url = recording_url
	
				if target_doctype and target_docname:
					call_log.link_with_reference_doc(target_doctype, target_docname)
					call_log.reference_doctype = target_doctype
					call_log.reference_docname = target_docname
					
				if active_lead_name and active_lead_name != target_docname:
					call_log.link_with_reference_doc("CRM Lead", active_lead_name)
					
				call_log.insert(ignore_permissions=True)
				synced_count += 1
			else:
				# If call log exists, we still want to update recording_url if it's missing
				recording_url = log.get("recording_url")
				if recording_url:
					existing_call_log = frappe.get_doc("CRM Call Log", call_id)
					if not existing_call_log.recording_url:
						existing_call_log.recording_url = recording_url
						existing_call_log.save(ignore_permissions=True)
						synced_count += 1
		except Exception as e:
			frappe.log_error(title="AIProf Telephony Sync Log Error", message=f"Error syncing call log: {str(e)}")
		
	if synced_count > 0 or len(updated_leads) > 0:
		frappe.db.commit()
		
	return {
		"status": "success", 
		"synced_count": synced_count,
		"leads_created": leads_created_count
	}
