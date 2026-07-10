import frappe

def main():
    frappe.init(site="crm.aiprof.com", sites_path="/home/frappe/frappe-bench/sites")
    frappe.connect()

    # Search case-insensitively for 'lilly' in first_name or last_name
    leads = frappe.get_all(
        "CRM Lead",
        filters={"first_name": ["like", "%lilly%"]},
        fields=["name", "first_name", "last_name", "status", "converted", "owner", "creation"]
    )
    
    if not leads:
        # Try searching by full name / name field
        leads = frappe.get_all(
            "CRM Lead",
            filters={"name": ["like", "%lilly%"]},
            fields=["name", "first_name", "last_name", "status", "converted", "owner", "creation"]
        )

    if leads:
        print(f"Found {len(leads)} lead(s) matching 'Lilly':")
        for lead in leads:
            print(f"- Name: {lead.first_name} {lead.last_name or ''}")
            print(f"  ID: {lead.name}")
            print(f"  Status: {lead.status}")
            print(f"  Converted: {lead.converted} (If 1, it is hidden from the main list by default)")
            print(f"  Owner: {lead.owner}")
            print(f"  Created: {lead.creation}")
    else:
        print("No leads matching 'Lilly' found in the database.")

if __name__ == "__main__":
    main()
