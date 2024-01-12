from dotenv import load_dotenv
from supabase import create_client, Client
from os import getenv

def auth():
    load_dotenv()
    url = getenv("SUPABASE_URL")
    key = getenv("SUPABASE_SERVICE_ROLE_KEY")
    supabase = create_client(url, key)
    return supabase

def write_results(package_name, type, user, repo_name, repo_url):
    supabase = auth()
    data = {"package_name": package_name,
            "type": type, "user": user,
            "repo_name": repo_name,
            "repo_url": repo_url}
    d = supabase.table("results").insert(data).execute()
    assert len(d.data) > 0

def fetch_user_app_settings(organization_id):
    supabase = auth()
    data = supabase.table("app").select(
        'installation_id,' +
        'provider,' +
        'repositories,' +
        'account_name' +
        'archived' +
        'forked'
        ).eq('organization_id', organization_id).execute()
    return data

def update_next_scan(organization_id, last_run, next_run):
    supabase = auth()
    data = supabase.table("reporting").update({
        "last_run": last_run,
        "next_run": next_run
    }).eq("organization_id", organization_id).execute()

def get_scheduled_runs(today):
    supabase = auth()
    data = supabase.table("reporting").select('organization_id').eq("next_run", today).execute()
    return data

def get_frequency(organization_id):
    supabase = auth()
    data = supabase.table("reporting").select('frequency').eq('organization_id', organization_id).execute()
    return data
