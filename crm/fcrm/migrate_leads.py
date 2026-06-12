import os
import frappe
from pymongo import MongoClient

def run():
	leads = frappe.get_all("CRM Lead", fields=["name", "mobile_no"])
	print(f"Aligning {len(leads)} leads...")

	# Initialize MongoDB connection
	mongo_uri = os.environ.get(
		"MONGO_URI", 
		"mongodb://myAdminUser:Hit%40042@172.17.0.1:27017/aiprof_telephony?authSource=admin"
	)
	if "localhost" in mongo_uri:
		mongo_uri = mongo_uri.replace("localhost", "172.17.0.1")
	elif "127.0.0.1" in mongo_uri:
		mongo_uri = mongo_uri.replace("127.0.0.1", "172.17.0.1")

	db = None
	try:
		client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
		db = client.get_database("aiprof_telephony")
	except Exception as e:
		print(f"Warning: Could not connect to MongoDB ({e}). Flags might not be updated.")

	updated_count = 0
	for lead_dict in leads:
		lead_name = lead_dict["name"]
		
		# Find the latest call log linked to this lead
		latest_call = frappe.db.sql(
			"""
			select cl.type, cl.start_time, cl.duration, cl.id, cl.telephony_medium
			from `tabCRM Call Log` cl
			left join `tabDynamic Link` dl on dl.parent = cl.name and dl.parenttype = 'CRM Call Log'
			where (
			    (cl.reference_doctype = 'CRM Lead' and cl.reference_docname = %s)
			    or (dl.link_doctype = 'CRM Lead' and dl.link_name = %s)
			  )
			order by cl.start_time desc
			limit 1
			""",
			(lead_name, lead_name),
			as_dict=True,
		)
		
		if latest_call:
			call = latest_call[0]
			lead = frappe.get_doc("CRM Lead", lead_name)
			
			# Map direction: set to inbound if this lead has ANY incoming call log
			has_inbound = frappe.db.sql(
				"""
				select cl.name
				from `tabCRM Call Log` cl
				left join `tabDynamic Link` dl on dl.parent = cl.name and dl.parenttype = 'CRM Call Log'
				where cl.type = 'Incoming'
				  and (
				    (cl.reference_doctype = 'CRM Lead' and cl.reference_docname = %s)
				    or (dl.link_doctype = 'CRM Lead' and dl.link_name = %s)
				  )
				limit 1
				""",
				(lead_name, lead_name),
			)
			lead.direction = "inbound" if has_inbound else "outbound"
			
			# Map Date and Time
			if call["start_time"]:
				import pytz
				dt = frappe.utils.to_datetime(call["start_time"])
				if dt:
					if dt.tzinfo is None:
						dt = pytz.utc.localize(dt)
					system_tz = pytz.timezone(frappe.utils.get_system_timezone())
					local_dt = dt.astimezone(system_tz)
					lead.call_date = local_dt.strftime("%Y-%m-%d")
					lead.call_time = local_dt.strftime("%H:%M:%S")
			
			# Map Duration
			if call["duration"] is not None:
				lead.call_duration = int(call["duration"])
				
			# Map Call Flag from MongoDB if Vobiz call
			if db is not None and call.get("telephony_medium") == "Vobiz" and call.get("id"):
				call_id = call.get("id")
				mongo_log = db.CallLogs.find_one({"$or": [{"call_id": call_id}, {"room_sid": call_id}]})
				if not mongo_log:
					try:
						from bson.objectid import ObjectId
						mongo_log = db.CallLogs.find_one({"_id": ObjectId(call_id)})
					except Exception:
						pass
				if mongo_log:
					flag_val = (mongo_log.get("analysis") or {}).get("flag")
					if flag_val:
						lead.call_flag = flag_val
			
			lead.save(ignore_permissions=True)
			updated_count += 1
			
	frappe.db.commit()
	print(f"Successfully aligned {updated_count} leads!")
