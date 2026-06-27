import frappe

def execute():
    statuses = {
        "Counselling": {
            "color": "gray",
            "type": "Open",
            "probability": 20,
            "position": 1,
        },
        "Negotiation": {
            "color": "yellow",
            "type": "Ongoing",
            "probability": 50,
            "position": 2,
        },
        "Ready to Close": {
            "color": "purple",
            "type": "Ongoing",
            "probability": 90,
            "position": 3,
        },
        "Won": {
            "color": "green",
            "type": "Won",
            "probability": 100,
            "position": 4,
        },
        "Lost": {
            "color": "red",
            "type": "Lost",
            "probability": 0,
            "position": 5,
        },
    }

    # Delete old statuses that are not in the new list
    existing_statuses = frappe.get_all("CRM Deal Status", pluck="name")
    for old_status in existing_statuses:
        if old_status not in statuses:
            try:
                frappe.delete_doc("CRM Deal Status", old_status, ignore_permissions=True, force=True)
                print(f"Deleted {old_status}")
            except Exception as e:
                print(f"Could not delete {old_status}: {e}")

    for status, details in statuses.items():
        if not frappe.db.exists("CRM Deal Status", status):
            doc = frappe.new_doc("CRM Deal Status")
            doc.deal_status = status
            doc.color = details["color"]
            doc.type = details["type"]
            doc.probability = details["probability"]
            doc.position = details["position"]
            doc.insert(ignore_permissions=True)
            print(f"Added {status}")
        else:
            doc = frappe.get_doc("CRM Deal Status", status)
            doc.color = details["color"]
            doc.type = details["type"]
            doc.probability = details["probability"]
            doc.position = details["position"]
            doc.save(ignore_permissions=True)
            print(f"Updated {status}")

    frappe.db.commit()
    print("Deal statuses updated successfully.")

if __name__ == "__main__":
    execute()
