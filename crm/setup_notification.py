import frappe

def run():
    if not frappe.db.exists('Notification', 'New Lead Assignment Alert'):
        doc = frappe.new_doc('Notification')
        doc.name = 'New Lead Assignment Alert'
        doc.subject = 'New Lead Assigned: {{ doc.lead_name or doc.first_name }}'
        doc.document_type = 'CRM Lead'
        doc.event = 'New'
        doc.channel = 'Email'
        doc.send_to_all_assignees = 0
        doc.append('recipients', {
            'receiver_by_document_field': 'lead_owner'
        })
        doc.message = '''<p>Hello,</p>
<p>A new lead has been assigned to you in the CRM.</p>
<p><strong>Lead Name:</strong> {{ doc.lead_name or doc.first_name }}<br>
<strong>Organization:</strong> {{ doc.organization or 'N/A' }}<br>
<strong>Mobile:</strong> {{ doc.mobile_no or 'N/A' }}</p>
<p>Please log in to the CRM to view the details.</p>'''
        doc.insert(ignore_permissions=True)
        print("Notification created successfully!")
    else:
        print("Notification already exists!")
    frappe.db.commit()
