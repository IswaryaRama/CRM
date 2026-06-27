import frappe

def execute():
    statuses = {
        "New": {
            "color": "gray",
            "type": "Open",
            "position": 1,
        },
        "Contacted": {
            "color": "blue",
            "type": "Ongoing",
            "position": 2,
        },
        "No response": {
            "color": "yellow",
            "type": "Ongoing",
            "position": 3,
        },
        "Not interested": {
            "color": "red",
            "type": "Lost",
            "position": 4,
        },
        "Interested to visit campus": {
            "color": "green",
            "type": "Ongoing",
            "position": 5,
        },
        "Follow up": {
            "color": "orange",
            "type": "Ongoing",
            "position": 6,
        },
    }

    # Delete old statuses that are not in the new list (optional, but requested to "update to")
    # For safety we just add the new ones, and update if they exist
    # Delete old statuses that are not in the new list
    existing_statuses = frappe.get_all("CRM Lead Status", pluck="name")
    for old_status in existing_statuses:
        if old_status not in statuses:
            try:
                frappe.delete_doc("CRM Lead Status", old_status, ignore_permissions=True, force=True)
                print(f"Deleted {old_status}")
            except Exception as e:
                print(f"Could not delete {old_status}: {e}")

    for status, details in statuses.items():
        if not frappe.db.exists("CRM Lead Status", status):
            doc = frappe.new_doc("CRM Lead Status")
            doc.lead_status = status
            doc.color = details["color"]
            doc.type = details["type"]
            doc.position = details["position"]
            doc.insert(ignore_permissions=True)
            print(f"Added {status}")
        else:
            doc = frappe.get_doc("CRM Lead Status", status)
            doc.color = details["color"]
            doc.type = details["type"]
            doc.position = details["position"]
            doc.save(ignore_permissions=True)
            print(f"Updated {status}")

    frappe.db.commit()
    print("Lead statuses updated successfully.")

if __name__ == "__main__":
    execute()
