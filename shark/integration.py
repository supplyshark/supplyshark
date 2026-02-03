from . import db
from datetime import datetime
from dotenv import load_dotenv
from os import getenv
from slack_bolt import App
import time

def slack_bot_auth():
    load_dotenv()
    token = getenv("SLACK_BOT_TOKEN")
    secret = getenv("SLACK_SIGNING_SECRET")
    return token, secret

def slack_result_msg(github, count, new_count, organization_id):
    date = datetime.now()

    attachment = [
        {
            "mrkdwn_in": ["text"],
            "color": "#36a64f",
            "ts": time.time(),
            "fields": [
                {
                    "title": "GitHub",
                    "value": github,
                    "short": True
                },
                {
                    "title": "Date",
                    "value": f"{date.month}-{date.day}-{date.year}",
                    "short": True
                },
                {
                    "title": "Total Results Found",
                    "value": count,
                    "short": True
                },
                {
                    "title": "New Results Found",
                    "value": new_count,
                    "short": True
                }
            ],
            "title": "View Results",
            "title_link": f"https://supplyshark.io/dashboard/{organization_id}/results/new"
        }
    ]

    return attachment

def slack_result_msg_home(github, count, new_count):
    date = datetime.now()

    attachment = [
        {
            "mrkdwn_in": ["text"],
            "color": "#36a64f",
            "ts": time.time(),
            "fields": [
                {
                    "title": "GitHub",
                    "value": github,
                    "short": True
                },
                {
                    "title": "Date",
                    "value": f"{date.month}-{date.day}-{date.year}",
                    "short": True
                },
                {
                    "title": "Total Results Found",
                    "value": count,
                    "short": True
                },
                {
                    "title": "New Results Found",
                    "value": new_count,
                    "short": True
                }
            ]
        }
    ]

    return attachment

def slack_write_message(channel_id, message, attachment):
    token, secret = slack_bot_auth()

    app = App(
        token=token,
        signing_secret=secret
    )

    try:
        resp = app.client.chat_postMessage(
            channel=channel_id,
            text=message,
            attachments=attachment
        )

    except:
        pass

def slack_write_message_cust(access_token, channel_id, message, attachment):
    _, secret = slack_bot_auth()

    app = App(
        token=access_token,
        signing_secret=secret
    )

    try:
        resp = app.client.chat_postMessage(
            channel=channel_id,
            text=message,
            attachments=attachment
        )
        print(resp)
    except:
        pass

def slack_write_alert_home(count, new_count, github):
    load_dotenv()
    channel_id = getenv("SHARK_CHANNEL_ID")
    message = f"Detected {count} potential vulnerabilities for GitHub: {github}"
    attachment = slack_result_msg_home(github, count, new_count)
    slack_write_message(channel_id, message, attachment)

def slack_write_alert_cust(organization_id, count, new_count, github):
    settings = db.get_slack_settings(organization_id)
    enabled = settings['slack_enabled']
    access_token = settings['slack_access_token']
    channel_id = settings['slack_channel_id']

    if enabled:
        message = f"Detected {count} potential vulnerabilities."
        attachment = slack_result_msg(github, count, new_count, organization_id)
        slack_write_message_cust(access_token, channel_id, message, attachment)
