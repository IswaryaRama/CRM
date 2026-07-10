import frappe

def test():
    from crm.permissions.org_hierarchy import _permission_query_conditions
    
    # Test as Sales User
    frappe.set_user("iswaryagajjala@gmail.com")
    cond = _permission_query_conditions("iswaryagajjala@gmail.com", "CRM Lead")
    if cond:
        sql = cond.get_sql(quote_char="`", secondary_quote_char="'")
        print(f"Sales User query condition SQL:\n{sql}")
    else:
        print("Sales User: NO conditions (sees everything)")

    # Test as Sales Manager
    frappe.set_user("iswaryagajjala@konamfoundation.org")
    cond = _permission_query_conditions("iswaryagajjala@konamfoundation.org", "CRM Lead")
    if cond:
        sql = cond.get_sql(quote_char="`", secondary_quote_char="'")
        print(f"\nSales Manager query condition SQL:\n{sql}")
    else:
        print("\nSales Manager: NO conditions (sees everything)")
