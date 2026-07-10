import frappe

def run():
    files = frappe.get_all('File', filters={'file_name': ['in', ['ai_prof.png', 'favicon.png']], 'is_private': 1})
    for f in files:
        doc = frappe.get_doc('File', f.name)
        doc.is_private = 0
        doc.save()
        print(f"Made {doc.file_name} public. New URL: {doc.file_url}")
    
    settings = frappe.get_doc('FCRM Settings')
    changed = False
    if settings.brand_logo and settings.brand_logo.startswith('/private/files/'):
        settings.brand_logo = settings.brand_logo.replace('/private/files/', '/files/')
        changed = True
    if settings.favicon and settings.favicon.startswith('/private/files/'):
        settings.favicon = settings.favicon.replace('/private/files/', '/files/')
        changed = True
    
    if changed:
        settings.save(ignore_permissions=True)
        print("Updated FCRM Settings.")
        
    frappe.db.commit()
    print("Done")
