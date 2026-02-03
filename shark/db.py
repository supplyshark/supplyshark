from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client
from os import getenv

def auth():
    load_dotenv()
    url = getenv("SUPABASE_URL")
    key = getenv("SUPABASE_SERVICE_ROLE_KEY")
    supabase = create_client(url, key)
    return supabase

def write_results(package_name, type, organization_id, repo_url, bug_url):
    supabase = auth()
    data = {"package_name": package_name,
            "type": type,
            "organization_id": organization_id,
            "repo_url": repo_url,
            "bug_url": bug_url}
    d = supabase.table("results").insert(data).execute()
    assert len(d.data) > 0

def check_result_exists(organization_id, package_name, type):
    supabase = auth()
    data = supabase.table("results").select('id', count='exact').match({
        "package_name": package_name,
        "organization_id": organization_id,
        "type": type,
        "resolved": False
    }).execute()
    return data

def check_result_new(id):
    supabase = auth()
    data = supabase.table("results").select(
        'repo_url,' +
        'bug_url'
        ).eq('id', id).execute()
    return data.data[0]

def delete_result(id):
    supabase = auth()
    d = supabase.table("results").delete().eq('id', id).execute()

def fetch_user_app_settings(organization_id):
    supabase = auth()
    data = supabase.table("github_app").select(
        'installation_id,' +
        'repositories,' +
        'account_name,' +
        'archived,' +
        'forked'
        ).eq('organization_id', organization_id).execute()
    return data.data[0]

def update_next_scan(organization_id, last_run, next_run):
    supabase = auth()
    data = supabase.table("supplyshark_config").update({
        "last_run": str(last_run),
        "next_run": str(next_run)
    }).eq("organization_id", organization_id).execute()

def insert_scan_stats(organization_id, count, new_count):
    supabase = auth()
    supabase.table("scans").insert({
        "organization_id": organization_id,
        "results": count,
        "new_results": new_count
    }).execute()

def today_date():
    date = datetime.now()
    return f"{date.month}-{date.day}-{date.year}"

def get_scheduled_runs():
    supabase = auth()
    today = today_date()
    data = supabase.table("supplyshark_config").select('organization_id').eq("next_run", today).execute()
    return [d['organization_id'] for d in data.data]

def get_frequency(organization_id):
    supabase = auth()
    data = supabase.table("supplyshark_config").select('frequency').eq('organization_id', organization_id).execute()
    return data.data[0]['frequency']

def get_org_id(organization_id):
    supabase = auth()
    data = supabase.table("organizations").select('id').eq('uuid', organization_id).execute()
    return data.data[0]['id']

def get_subscription_id(organization_id):
    org_id = get_org_id(organization_id)
    supabase = auth()
    data = supabase.table("organizations_subscriptions").select('subscription_id').eq('organization_id', org_id).execute()
    return data.data[0]['subscription_id']

def get_price_id(subscription_id):
    supabase = auth()
    data = supabase.table('subscriptions').select('price_id').eq('id', subscription_id).execute()
    return data.data[0]['price_id']

def get_status(subscription_id):
    supabase = auth()
    data = supabase.table('subscriptions').select('status').eq('id', subscription_id).execute()
    return data.data[0]['status']

def is_active(organization_id):
    subscription_id = get_subscription_id(organization_id)
    status = get_status(subscription_id)
    if status == "active":
        return True
    else:
        return False

def get_subscription_name(organization_id):
    subscription_id = get_subscription_id(organization_id)
    price_id = get_price_id(subscription_id)

    load_dotenv()

    if price_id == getenv("PLAN_STARTER"):
        return "starter"
    elif price_id == getenv("PLAN_PRO"):
        return "pro"
    elif price_id == getenv("PLAN_PREMIUM"):
        return "premium"

def get_slack_settings(organization_id):
    supabase = auth()
    data = supabase.table('supplyshark_config').select('slack_enabled,slack_access_token,slack_channel_id').eq('organization_id', organization_id).execute()
    return data.data[0]

def get_team_email_settings(organization_id):
    supabase = auth()
    data = supabase.table('supplyshark_config').select('team_email_enabled,team_email').eq('organization_id', organization_id).execute()
    return data.data[0]