# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class CRMVobizSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		enabled: DF.Check
		record_calls: DF.Check
		auth_id: DF.Data | None
		api_password: DF.Password | None
		app_id: DF.Data | None
		webhook_url_override: DF.Data | None
		registered_webhook_url: DF.Data | None
	# end: auto-generated types

	@frappe.whitelist()
	def fetch_applications(self):
		import requests
		auth_id = self.auth_id
		api_password = self.get_password("api_password")
		if not auth_id or not api_password:
			frappe.throw(_("Please enter Auth ID and API Password first."))

		url = f"https://api.vobiz.ai/api/v1/Account/{auth_id}/Application/"
		headers = {
			"X-Auth-ID": auth_id,
			"X-Auth-Token": api_password,
			"Content-Type": "application/json"
		}
		try:
			response = requests.get(url, headers=headers, timeout=10)
			response.raise_for_status()
			apps_data = response.json()
			return apps_data
		except Exception as e:
			frappe.log_error(message=str(e), title="Vobiz API Error")
			frappe.throw(_("Failed to fetch applications from Vobiz: {0}").format(str(e)))

	@frappe.whitelist()
	def register_webhook(self, app_id):
		import requests
		auth_id = self.auth_id
		api_password = self.get_password("api_password")
		if not auth_id or not api_password:
			frappe.throw(_("Please configure Vobiz Auth ID and API Password first."))

		webhook_url = self.get_webhook_url()
		if self.webhook_url_override:
			override = self.webhook_url_override.strip().rstrip("/")
			if not (override.startswith("http://") or override.startswith("https://")):
				override = "https://" + override
			if "/api/method/" in override:
				hangup_url = override.replace(".voice", ".hangup")
			else:
				hangup_url = override + "/api/method/crm.integrations.vobiz.api.hangup"
		else:
			hangup_url = get_public_url("/api/method/crm.integrations.vobiz.api.hangup")
		
		url = f"https://api.vobiz.ai/api/v1/Account/{auth_id}/Application/{app_id}/"
		headers = {
			"X-Auth-ID": auth_id,
			"X-Auth-Token": api_password,
			"Content-Type": "application/json"
		}
		payload = {
			"answer_url": webhook_url,
			"answer_method": "POST",
			"hangup_url": hangup_url,
			"hangup_method": "POST"
		}
		try:
			response = requests.post(url, headers=headers, json=payload, timeout=10)
			if response.status_code >= 400:
				error_details = response.text
				try:
					err_json = response.json()
					if isinstance(err_json, dict):
						error_details = err_json.get("message") or err_json.get("error") or err_json.get("error_message") or response.text
				except Exception:
					pass
				frappe.throw(_("Vobiz API Error: {0}").format(error_details))

			response.raise_for_status()
			
			self.db_set("app_id", app_id)
			self.db_set("registered_webhook_url", webhook_url)
			
			return {"status": "success", "webhook_url": webhook_url}
		except Exception as e:
			frappe.log_error(message=str(e), title="Vobiz Webhook Registration Error")
			frappe.throw(_("Failed to register webhook with Vobiz: {0}").format(str(e)))

	@frappe.whitelist()
	def get_webhook_url(self):
		if self.webhook_url_override:
			override = self.webhook_url_override.strip().rstrip("/")
			if not (override.startswith("http://") or override.startswith("https://")):
				override = "https://" + override
			if "/api/method/" in override:
				return override
			return override + "/api/method/crm.integrations.vobiz.api.voice"
		return get_public_url("/api/method/crm.integrations.vobiz.api.voice")


def get_public_url(path: str):
	from frappe.utils import get_url
	import frappe

	# Try to get hostname from incoming request first (handles dynamic proxy/ngrok headers)
	host = None
	if hasattr(frappe.local, "request") and frappe.local.request:
		req_host = frappe.local.request.headers.get("X-Forwarded-Host") or frappe.local.request.headers.get("Host")
		if req_host:
			# If the request host is local (localhost, 127.0.0.1, crm.localhost), check if site config has a public URL
			is_req_local = any(x in req_host for x in ["localhost", "127.0.0.1", "0.0.0.0", "crm.localhost"])
			if is_req_local:
				configured_url = get_url()
				is_config_local = any(x in configured_url for x in ["localhost", "127.0.0.1", "0.0.0.0", "crm.localhost"])
				if not is_config_local:
					url = configured_url.split(":8", 1)[0]
					return url.rstrip("/") + path

			protocol = frappe.local.request.headers.get("X-Forwarded-Proto") or "http"
			return f"{protocol}://{req_host}{path}"

	# Fallback to get_url()
	url = get_url().split(":8", 1)[0]
	return url.rstrip("/") + path

