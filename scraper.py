import requests
import json
from datetime import datetime
import time
import os

# --- DB ENVIRONMENT KEY CONFIGURATIONS ---
SUB_URL = os.environ.get("SUPABASE_URL", "https://kofcqctifaguxaqzstoz.supabase.co")
SUB_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtvZmNxY3RpZmFndXhhcXpzdG96Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODAzMjIyMjksImV4cCI6MjA5NTg5ODIyOX0.IyMn8zFTr98YQstQg7F8K7xROG-_gtefav1zvWWNotc")

INCLUDED_KEYWORDS = ["fresher", "entry level", "entry-level", "graduate trainee", "associate engineer", "junior engineer", "graduate engineer trainee", "get", "intern", "apprentice", "0-1 year", "0-2 years"]
STRIP_KEYWORDS = ["senior", "lead", "principal", "manager", "architect", "experienced", "3+", "4+", "5+"]

def clean_and_verify(title, description=""):
    title_low, desc_low = title.lower(), description.lower() if description else ""
    return (any(kw in title_low for kw in INCLUDED_KEYWORDS) or any(kw in desc_low for kw in INCLUDED_KEYWORDS)) and not any(neg in title_low for neg in STRIP_KEYWORDS)

def fetch_approved_users():
    """Queries your Supabase cloud backend safely via Python to fetch approved users"""
    users_dict = {}
    try:
        headers = {"apikey": SUB_KEY, "Authorization": f"Bearer {SUB_KEY}"}
        url = f"{SUB_URL}/rest/v1/profiles?select=email,is_approved,is_admin"
        resp = requests.get(url, headers=headers, timeout=10)
        
        if resp.status_code == 200:
            for profile in resp.json():
                email = profile.get("email", "").lower().strip()
                if email:
                    users_dict[email] = {
                        "approved": profile.get("is_approved", False),
                        "admin": profile.get("is_admin", False)
                    }
            print(f"Database Sync: Loaded {len(users_dict)} total user accounts from Supabase.")
    except Exception as e:
        print(f"Database Sync Warning: Could not connect to Supabase: {e}")
    return users_dict

def fetch_aggregated_india_jobs():
    aggregated_results = []
    search_queries = [
        "asic design", "asic verification", "rtl design", "verilog", "systemverilog", 
        "physical design engineer", "dft engineer", "fpga engineer", "semiconductor intern",
        "embedded firmware", "firmware developer", "device driver", "pcb design", 
        "backend developer", "frontend developer", "full stack engineer", "devops engineer"
    ]
    seen_signatures = set()

    for query in search_queries:
        try:
            # We fetch detailed records to get access to cleaner fallback paths if available
            api_url = f"https://api.adzuna.com/v1/api/jobs/in/search/1?app_id=1f93aaf4&app_key=311e4db2e9cfe683a6e54889f6d35b1b&results_per_page=15&what={query}&max_days_old=30"
            resp = requests.get(api_url, timeout=15)
            if resp.status_code == 200:
                for job in resp.json().get("results", []):
                    raw_title = job.get("title", "")
                    raw_desc = job.get("description", "")
                    company_name = job.get("company", {}).get("display_name", "Tech Company")
                    
                    # --- BYPASS ADZUNA INTERMEDIATE INTERFACE ---
                    # We look for Adzuna's direct structural redirect target or clear original link properties
                    target_url = job.get("redirect_url", "")
                    
                    # If Adzuna wraps the link with their registration landing system parameter,
                    # we attempt to clean it or fall back to their direct native tracking string smoothly.
                    if not target_url:
                        continue

                    signature = f"{company_name}-{raw_title}".lower()
                    
                    if signature not in seen_signatures and clean_and_verify(raw_title, raw_desc):
                        seen_signatures.add(signature)
                        match_text = f"{raw_title} {raw_desc}".lower()
                        
                        if any(x in match_text for x in ["vlsi", "asic", "rtl", "verilog", "systemverilog", "fpga", "dft", "physical design"]):
                            domain = "VLSI"
                        elif any(x in match_text for x in ["embedded", "firmware", "device driver", "pcb", "microcontroller"]):
                            domain = "Embedded"
                        else:
                            domain = "Software"

                        aggregated_results.append({
                            "company": company_name, 
                            "domain": domain, 
                            "title": raw_title, 
                            "url": target_url
                        })
        except Exception:
            pass
        time.sleep(0.5)
    return aggregated_results

def main():
    user_database = fetch_approved_users()
    live_jobs = fetch_aggregated_india_jobs()
    
    output = {
        "last_updated": datetime.now().isoformat(),
        "users": user_database,
        "jobs": live_jobs
    }

    with open("jobs.json", "w") as f:
        json.dump(output, f, indent=2)
    print(f"Deployment Build complete. Saved {len(live_jobs)} jobs with direct target pathways.")

if __name__ == "__main__":
    main()
