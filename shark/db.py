from dotenv import load_dotenv
from supabase import create_client, Client
from os import getenv

def auth():
    url = getenv("SUPABASE_URL")
    key = getenv("SUPABASE_KEY")
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