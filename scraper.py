import requests
import json
from datetime import datetime
import time

# Comprehensive Fresher & Entry-Level Indicators
INCLUDED_KEYWORDS = [
    "fresher", "entry level", "entry-level", "graduate trainee", "associate engineer",
    "junior engineer", "graduate engineer trainee", "get", "et", "software trainee",
    "intern", "apprentice", "0-1 year", "0-2 years", "2025 passout", "2026 passout", "2027 passout"
]

# Strict exclusionary terms to prevent senior roles from leaking in
STRIP_KEYWORDS = [
    "senior", "lead", "principal", "manager", "architect", "experienced", "years experience", 
    "3+", "4+", "5+", "sr.", "tech lead", "team lead"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

def clean_and_verify(title, description=""):
    title_low = title.lower()
    desc_low = description.lower() if description else ""
    
    # Verify it targets early-career applicants
    has_fresher = any(kw in title_low for kw in INCLUDED_KEYWORDS) or any(kw in desc_low for kw in INCLUDED_KEYWORDS)
    # Ensure it's not a senior position
    has_senior = any(neg in title_low for neg in STRIP_KEYWORDS)
    
    return has_fresher and not has_senior

def fetch_aggregated_india_jobs():
    aggregated_results = []
    
    # NATIONWIDE EXPANDED SEARCH QUERY PIPELINE
    search_queries = [
        # === VLSI / ASIC / CHIP DESIGN TRACKS ===
        "asic design", "asic verification", "rtl design", "verilog", "systemverilog", 
        "physical design engineer", "dft engineer", "fpga engineer", "semiconductor intern", 
        "analog layout", "soc architecture", "synthesis engineering",
        
        # === EMBEDDED SYSTEMS / ELECTRONICS TRACKS ===
        "embedded firmware", "firmware developer", "device driver", "pcb design", 
        "hardware validation", "microcontroller engineer", "iot intern", "electronics trainee",
        
        # === SOFTWARE / DIGITAL TECH TRACKS ===
        "backend developer", "frontend developer", "full stack engineer", "qa automation engineer", 
        "devops engineer", "data engineer trainee", "cybersecurity analyst intern", "cloud engineer associate"
    ]
    
    seen_signatures = set()

    for query in search_queries:
        try:
            # Added max_days_old=30 parameter to keep the job feed fresh
            api_url = f"https://api.adzuna.com/v1/api/jobs/in/search/1?app_id=1f93aaf4&app_key=311e4db2e9cfe683a6e54889f6d35b1b&results_per_page=25&what={query}&max_days_old=30"
            resp = requests.get(api_url, headers=HEADERS, timeout=15)
            
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("results", [])
                
                for job in results:
                    raw_title = job.get("title", "")
                    raw_desc = job.get("description", "")
                    company_name = job.get("company", {}).get("display_name", "Tech Company")
                    target_url = job.get("redirect_url", "")
                    
                    signature = f"{company_name}-{raw_title}".lower()
                    
                    if signature not in seen_signatures and clean_and_verify(raw_title, raw_desc):
                        seen_signatures.add(signature)
                        
                        # Inspect both the title and text snippet for proper domain categorization
                        match_text = f"{raw_title} {raw_desc}".lower()
                        
                        # VLSI & ASIC Custom Sub-categories
                        vlsi_tags = ["vlsi", "asic", "rtl", "verilog", "systemverilog", "semiconductor", "fpga", "physical design", "dft", "synthesis", "hardware design", "digital design", "analog layout", "soc"]
                        # Embedded Sub-categories
                        embedded_tags = ["embedded", "firmware", "device driver", "pcb", "schematic", "validation", "iot", "microcontroller", "hardware engineering", "electronics"]
                        
                        if any(x in match_text for x in vlsi_tags):
                            domain = "VLSI"
                        elif any(x in match_text for x in embedded_tags):
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
            print(f"Skipping lookup segment '{query}': {e}")
        time.sleep(1.2) # Avoid hitting API gateway rate limit alerts
        
    return aggregated_results

def main():
    print("Initializing expanded nationwide fresher career lookup sync...")
    live_jobs = fetch_aggregated_india_jobs()
    
    output = {
        "last_updated": datetime.now().isoformat(),
        "total": len(live_jobs),
        "jobs": live_jobs
    }

    with open("jobs.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"Sync complete. Compiled {len(live_jobs)} verified positions across all custom tracks.")

if __name__ == "__main__":
    main()
