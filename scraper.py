import requests
import json
from datetime import datetime
import time

INCLUDED_KEYWORDS = [
    "fresher", "entry level", "entry-level", "graduate trainee", "associate engineer",
    "junior engineer", "graduate engineer trainee", "get", "et", "software trainee",
    "intern", "apprentice", "0-1 year", "0-2 years", "2025 passout", "2026 passout", "2027 passout"
]

STRIP_KEYWORDS = [
    "senior", "lead", "principal", "manager", "architect", "experienced", "years experience", 
    "3+", "4+", "5+", "sr.", "tech lead", "team lead"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

def clean_and_verify(title):
    title_low = title.lower()
    has_fresher = any(kw in title_low for kw in INCLUDED_KEYWORDS)
    has_senior = any(neg in title_low for neg in STRIP_KEYWORDS)
    return has_fresher and not has_senior

def fetch_aggregated_india_jobs():
    aggregated_results = []
    search_queries = ["fresher engineer", "graduate trainee", "software intern", "associate developer"]
    seen_signatures = set()

    for query in search_queries:
        try:
            # Nationwide Indian Job Aggregator Stream Engine
            # Updated with your personal dedicated API keys
            api_url = f"https://api.adzuna.com/v1/api/jobs/in/search/1?app_id=1f93aaf4&app_key=311e4db2e9cfe683a6e54889f6d35b1b&results_per_page=50&what={query}"
            resp = requests.get(api_url, headers=HEADERS, timeout=15)
            
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("results", [])
                
                for job in results:
                    raw_title = job.get("title", "")
                    company_name = job.get("company", {}).get("display_name", "Tech Company")
                    target_url = job.get("redirect_url", "")
                    
                    signature = f"{company_name}-{raw_title}".lower()
                    
                    if signature not in seen_signatures and clean_and_verify(raw_title):
                        seen_signatures.add(signature)
                        
                        title_check = raw_title.lower()
                        if any(x in title_check for x in ["vlsi", "asic", "rtl", "verilog", "semiconductor"]):
                            domain = "VLSI"
                        elif any(x in title_check for x in ["embedded", "iot", "firmware", "microcontroller"]):
                            domain = "Embedded"
                        else:
                            domain = "Software"

                        aggregated_results.append({
                            "company": company_name,
                            "domain": domain,
                            "title": raw_title,
                            "url": target_url,
                            "company_careers": target_url,
                            "found_at": datetime.now().isoformat()
                        })
        except Exception as e:
            print(f"Skipping lookup for segment '{query}': {e}")
        time.sleep(1)
        
    return aggregated_results

def main():
    print("Starting nationwide fresher career lookup cycle...")
    live_jobs = fetch_aggregated_india_jobs()
    
    output = {
        "last_updated": datetime.now().isoformat(),
        "total": len(live_jobs),
        "jobs": live_jobs
    }

    with open("jobs.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"Sync complete. Compiled {len(live_jobs)} verified positions.")

if __name__ == "__main__":
    main()
