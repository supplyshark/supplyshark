from . import db
from dotenv import load_dotenv
from os import getenv
from sendgrid.helpers.mail import *
import sendgrid

def send(email, count, account, org_id):
    load_dotenv()
    api_key = getenv("SENDGRID_API_KEY")

    sg = sendgrid.SendGridAPIClient(api_key=api_key)
    from_email = Email("SupplyShark <no-reply@supplyshark.io>")
    to_email = To(email)
    subject = f"SupplyShark found {count} potential vulnerabilities."
    mail = Mail(from_email, to_email, subject)
    
    mail.dynamic_template_data = {
        "count": count,
        "account": account,
        "orgId": org_id
    }

    mail.template_id = "d-c73ab1c20923465e875fcb6b80f347bc"

    sg.client.mail.send.post(request_body=mail.get())

def send_email(org_id, count, account):
    settings = db.get_team_email_settings(org_id)
    if settings['team_email_enabled']:
        team_email = settings['team_email']
        send(team_email, count, account, org_id)