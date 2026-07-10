import frappe

def execute():
    # Rename old status if they exist
    for old_name, new_name in [
        ("Interested in Webinar", "Registered for webinar"),
        ("Interested in webinar", "Registered for webinar"),
        ("Not interested in Webinar", "Not registered in webinar"),
        ("Not interested in webinar", "Not registered in webinar"),
        ("Not paid", "Deal lost"),
        ("Not Paid", "Deal lost")
    ]:
        if frappe.db.exists("CRM Lead Status", old_name) and not frappe.db.exists("CRM Lead Status", new_name):
            frappe.rename_doc("CRM Lead Status", old_name, new_name, force=True)
            print(f"Renamed status {old_name} to {new_name}")

    statuses = {
        "New": {
            "color": "gray",
            "type": "Open",
            "position": 1,
        },
        "Registered for webinar": {
            "color": "blue",
            "type": "Ongoing",
            "position": 2,
        },
        "Not registered in webinar": {
            "color": "red",
            "type": "Lost",
            "position": 3,
        },
        "Webinar attended": {
            "color": "green",
            "type": "Ongoing",
            "position": 4,
        },
        "Webinar not attended": {
            "color": "yellow",
            "type": "Ongoing",
            "position": 5,
        },
        "Test taken": {
            "color": "blue",
            "type": "Ongoing",
            "position": 6,
        },
        "Test not taken": {
            "color": "yellow",
            "type": "Ongoing",
            "position": 7,
        },
        "Campus visited": {
            "color": "green",
            "type": "Ongoing",
            "position": 8,
        },
        "Campus not visited": {
            "color": "yellow",
            "type": "Ongoing",
            "position": 9,
        },
        "Deal lost": {
            "color": "red",
            "type": "Lost",
            "position": 10,
        },
    }

    # Delete old statuses that are not in the new list (optional, but requested to "update to")
    # For safety we just add the new ones, and update if they exist
    for status, details in statuses.items():
        if not frappe.db.exists("CRM Lead Status", status):
            doc = frappe.new_doc("CRM Lead Status")
            doc.lead_status = status
            doc.color = details["color"]
            doc.type = details["type"]
            doc.position = details["position"]
            doc.insert()
            print(f"Added {status}")
        else:
            doc = frappe.get_doc("CRM Lead Status", status)
            doc.color = details["color"]
            doc.type = details["type"]
            doc.position = details["position"]
            doc.save()
            print(f"Updated {status}")

    frappe.db.commit()
    print("Lead statuses updated successfully.")

if __name__ == "__main__":
    execute()
