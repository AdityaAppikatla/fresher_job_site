import requests
import json
from datetime import datetime
import time
import os
import re

# --- DB ENVIRONMENT KEY CONFIGURATIONS ---
SUB_URL = os.environ.get("SUPABASE_URL", "https://kofcqctifaguxaqzstoz.supabase.co")
SUB_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtvZmNxY3RpZmFndXhhcXpzdG96Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODAzMjIyMjksImV4cCI6MjA5NTg5ODIyOX0.IyMn8zFTr98YQstQg7F8K7xROG-_gtefav1zvWWNotc")

# Broad fresher matching keywords
INCLUDED_KEYWORDS = ["fresher", "entry level", "entry-level", "graduate", "trainee", "associate", "junior", "intern", "apprentice", "0-1 year", "0-2 years", "no experience"]

# Titles containing these are blocked immediately
STRICT_TITLE_BLOCKS = ["senior", "lead", "principal", "manager", "architect", "sr.", "mid-level"]

def clean_and_verify(title, description=""):
    title_low = title.lower()
    desc_low = description.lower() if description else ""
    full_text = f"{title_low} {desc_low}"
    
    # 1. If the job title explicitly says Senior/Lead/Manager, throw it out immediately
    if any(block in title_low for block in STRICT_TITLE_BLOCKS):
        return False
        
    # 2. Strict regex block to throw out high experience numbers (e.g., 3+ years, 4-6 yrs, 5 years)
    # It allows 0, 1, or 2 years, but blocks 3 through 15 years
    exp_pattern = r'([3-9]|10|12|15)\s*(to|-|\+)?\s*\d*\s*(year|yr|exp)'
    if re.search(exp_pattern, full_text):
        return False

    # 3. Acceptance check: If the title looks like an entry position, or description mentions fresher terms, it passes!
    return any(kw in title_low for kw in INCLUDED_KEYWORDS) or any(kw in desc_low for kw in INCLUDED_KEYWORDS) or "engineer" in title_low

def fetch_approved_users():
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
    except Exception:
        pass
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
        # Loop through pages 1 and 2 for EVERY query to pull way more job listings across India
        for page in [1, 2]:
            try:
                api_url = f"https://api.adzuna.com/v1/api/jobs/in/search/{page}?app_id=1f93aaf4&app_key=311e4db2e9cfe683a6e54889f6d35b1b&results_per_page=50&what={query}&max_days_old=30"
                resp = requests.get(api_url, timeout=15)
                if resp.status_code == 200:
                    results = resp.json().get("results", [])
                    if not results:
                        break # No more jobs for this query, break page loop
                        
                    for job in results:
                        raw_title = job.get("title", "")
                        raw_desc = job.get("description", "")
                        company_name = job.get("company", {}).get("display_name", "Tech Company")
                        
                        raw_url = job.get("redirect_url", "")
                        if not raw_url:
                            continue
                            
                        clean_url = raw_url
                        match = re.search(r'redirect_to=([^&]+)', raw_url)
                        if match:
                            from urllib.parse import unquote
                            extracted_url = unquote(match.group(1))
                            if extracted_url.startswith('http'):
                                clean_url = extracted_url

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
                                "company": company_name, "domain": domain, "title": raw_title, "url": clean_url
                            })
            except Exception:
                pass
            time.sleep(0.3)
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
    print(f"Volume sync complete. Saved {len(live_jobs)} verified fresher positions.")

if __name__ == "__main__":
    main()
