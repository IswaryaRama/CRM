__version__ = "2.0.0-dev"
__title__ = "AIProf CRM"

import sys
import frappe

try:
	import frappe.tests
	from frappe.tests.utils import FrappeTestCase
	import frappe.tests.utils
	import frappe.test_runner
	
	if not hasattr(frappe.tests, "IntegrationTestCase"):
		frappe.tests.IntegrationTestCase = FrappeTestCase
		sys.modules["frappe.tests"].IntegrationTestCase = FrappeTestCase
		
	if not hasattr(frappe.tests, "UnitTestCase"):
		frappe.tests.UnitTestCase = FrappeTestCase
		sys.modules["frappe.tests"].UnitTestCase = FrappeTestCase
		
	if not hasattr(frappe.tests.utils, "make_test_records"):
		frappe.tests.utils.make_test_records = frappe.test_runner.make_test_records
except ImportError:
	pass

import frappe.utils
if not hasattr(frappe.utils, "to_datetime"):
	frappe.utils.to_datetime = frappe.utils.get_datetime


# Monkeypatch make_post_request for WhatsApp Mock Testing
try:
	import frappe.integrations.utils
	original_make_post_request = frappe.integrations.utils.make_post_request

	def custom_make_post_request(*args, **kwargs):
		url = args[0] if args else kwargs.get("url", "")
		headers = kwargs.get("headers") or {}
		auth_header = headers.get("authorization") or headers.get("Authorization") or ""
		if "mock" in url or "mock" in auth_header:
			import json
			import frappe
			# Log intercepted mock request to the Error Log
			frappe.log_error(
				title="Mock WhatsApp API Request Intercepted",
				message=f"URL: {url}\nHeaders: {headers}\nData: {kwargs.get('data')}"
			)
			return {
				"messaging_product": "whatsapp",
				"contacts": [{"input": "test", "wa_id": "test"}],
				"messages": [{"id": f"wamid.mock_{frappe.generate_hash(length=16)}"}]
			}
		return original_make_post_request(*args, **kwargs)

	frappe.integrations.utils.make_post_request = custom_make_post_request
except Exception:
	pass

