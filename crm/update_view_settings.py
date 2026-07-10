import frappe
import json

settings_list = frappe.get_all("CRM View Settings", filters={"dt": "CRM Lead"}, fields=["name", "columns", "rows"])
for s in settings_list:
    try:
        cols = json.loads(s.columns)
        new_cols = [c for c in cols if c.get("key") != "call_time"]
        
        rows = json.loads(s.rows)
        new_rows = [r for r in rows if r != "call_time"]
        
        frappe.db.set_value("CRM View Settings", s.name, {
            "columns": json.dumps(new_cols),
            "rows": json.dumps(new_rows)
        })
        print(f"Updated {s.name}")
    except Exception as e:
        print(f"Error updating {s.name}: {e}")

frappe.db.commit()
print("SUCCESS")
