import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import time
from urllib.parse import urljoin

COMPANIES = [
    # Semiconductor / VLSI
    {"name": "NVIDIA", "url": "https://nvidia.eightfold.ai/careers", "domain": "VLSI"},
    {"name": "Tessolve", "url": "https://tessolve.com/careers/", "domain": "VLSI"},
    {"name": "Sankalp Semiconductor", "url": "https://sankalpct.com/careers/", "domain": "VLSI"},
    {"name": "eInfochips", "url": "https://www.einfochips.com/careers/", "domain": "VLSI"},
    {"name": "Entuple Technologies", "url": "https://entuple.com/careers/", "domain": "VLSI"},
    {"name": "Amitek", "url": "https://www.amitek.in/careers", "domain": "VLSI"},
    {"name": "Likitha Semiconductor", "url": "https://likithasemiconductor.com/careers", "domain": "VLSI"},
    {"name": "Centre for Development of Advanced Computing", "url": "https://www.cdac.in/index.aspx?id=career", "domain": "VLSI"},
    {"name": "BEL", "url": "https://bel-india.in/careers/", "domain": "VLSI"},
    {"name": "SION Semiconductors", "url": "https://sionsemi.com/careers", "domain": "VLSI"},
    {"name": "Radiant Semiconductors", "url": "https://radiantsemi.com/careers", "domain": "VLSI"},
    {"name": "Mirafra Technologies", "url": "https://mirafra.com/careers/", "domain": "VLSI"},
    {"name": "MosChip", "url": "https://moschip.com/careers/", "domain": "VLSI"},
    {"name": "XtremeSilica Technologies", "url": "https://xtremesilica.com/careers", "domain": "VLSI"},
    {"name": "KeenSemi", "url": "https://keensemi.com/careers", "domain": "VLSI"},
    {"name": "Green Semiconductors", "url": "https://greensemi.in/careers", "domain": "VLSI"},
    {"name": "Chipspirit", "url": "https://chipspirit.com/careers", "domain": "VLSI"},
    {"name": "PrimeSoc Technologies", "url": "https://primesoc.com/careers", "domain": "VLSI"},
    {"name": "leadIC Design", "url": "https://leadicdesign.com/careers", "domain": "VLSI"},
    {"name": "PulseWave Semiconductor", "url": "https://pulsewave.in/careers", "domain": "VLSI"},
    {"name": "ROUTE2SOC Technologies", "url": "https://route2soc.com/careers", "domain": "VLSI"},
    # Embedded
    {"name": "Embien Technologies", "url": "https://embien.com/careers/", "domain": "Embedded"},
    {"name": "Delphi TVS", "url": "https://www.delphitvs.com/careers", "domain": "Embedded"},
    {"name": "Bosch India", "url": "https://www.bosch.in/careers/", "domain": "Embedded"},
    {"name": "Continental India", "url": "https://www.continental-jobs.com/", "domain": "Embedded"},
    {"name": "Tata Elxsi", "url": "https://www.tataelxsi.com/careers/", "domain": "Embedded"},
    # Software
    {"name": "TCS", "url": "https://www.tcs.com/careers/india", "domain": "Software"},
    {"name": "Infosys", "url": "https://career.infosys.com/", "domain": "Software"},
    {"name": "Wipro", "url": "https://careers.wipro.com/", "domain": "Software"},
    {"name": "HCL Technologies", "url": "https://www.hcltech.com/careers", "domain": "Software"},
    {"name": "Tech Mahindra", "url": "https://careers.techmahindra.com/", "domain": "Software"},
    {"name": "Mphasis", "url": "https://careers.mphasis.com/", "domain": "Software"},
    {"name": "Cognizant", "url": "https://careers.cognizant.com/india", "domain": "Software"},
    {"name": "Accenture India", "url": "https://www.accenture.com/in-en/careers", "domain": "Software"},
    {"name": "Capgemini India", "url": "https://www.capgemini.com/in-en/careers/", "domain": "Software"},
    {"name": "L&T Technology Services", "url": "https://www.ltts.com/careers", "domain": "Software"},
]

FRESHER_KEYWORDS = [
    "fresher", "graduate", "trainee", "junior", "entry level", "entry-level",
    "0-1 year", "0 year", "0-2 year", "intern", "apprentice", "associate engineer",
    "graduate engineer", "get", "campus", "2025 passout", "2026 passout", "2027 passout"
]

NEGATIVE_KEYWORDS = [
    "senior", "lead", "principal", "manager", "architect", "experienced", "years experience", "5+", "3+"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def is_fresher_role(text):
    text_lower = text.lower()
    has_fresher = any(kw in text_lower for kw in FRESHER_KEYWORDS)
    has_negative = any(neg in text_lower for neg in NEGATIVE_KEYWORDS)
    return has_fresher and not has_negative

def scrape_company(company):
    results = []
    try:
        resp = requests.get(company["url"], headers=HEADERS, timeout=15, verify=True)
        soup = BeautifulSoup(resp.text, "html.parser")
        seen_titles = set()
        
        # Pull text from hyperlink components rather than broad structural tags
        links_found = soup.find_all("a")
        
        for link in links_found:
            text = link.get_text(separator=" ", strip=True)
            url_path = link.get("href", "").strip()
            
            if 6 < len(text) < 90:
                if is_fresher_role(text):
                    clean_title = " ".join(text.split())
                    
                    if clean_title not in seen_titles:
                        seen_titles.add(clean_title)
                        
                        # Fix relative directory links
                        if url_path.startswith("http"):
                            job_url = url_path
                        elif url_path.startswith("/"):
                            job_url = urljoin(company["url"], url_path)
                        else:
                            job_url = company["url"]

                        results.append({
                            "company": company["name"],
                            "domain": company["domain"],
                            "title": clean_title,
                            "url": job_url,
                            "company_careers": company["url"],
                            "found_at": datetime.now().isoformat()
                        })

        if not results:
            results.append({
                "company": company["name"],
                "domain": company["domain"],
                "title": "Check career portal for active openings",
                "url": company["url"],
                "company_careers": company["url"],
                "found_at": datetime.now().isoformat(),
                "manual_check": True
            })

    except Exception as e:
        results.append({
            "company": company["name"],
            "domain": company["domain"],
            "title": "Portal update in progress — check manually",
            "url": company["url"],
            "company_careers": company["url"],
            "found_at": datetime.now().isoformat(),
            "error": str(e)
        })

    return results

def send_email(all_jobs):
    service_id = os.environ.get("EMAILJS_SERVICE_ID", "")
    template_id = os.environ.get("EMAILJS_TEMPLATE_ID", "")
    public_key = os.environ.get("EMAILJS_PUBLIC_KEY", "")
    private_key = os.environ.get("EMAILJS_PRIVATE_KEY", "")
    recipient = os.environ.get("NOTIFY_EMAIL", "")

    if not all([service_id, template_id, public_key, private_key, recipient]):
        print("Email skipped — one or more secrets missing")
        return

    fresher_jobs = [j for j in all_jobs if not j.get("manual_check") and not j.get("error")]
    summary = "\n".join([f"• {j['company']}: {j['title']}" for j in fresher_jobs[:15]]) if fresher_jobs else "No specific fresher roles detected today — check the dashboard."

    payload = {
        "service_id": service_id,
        "template_id": template_id,
        "user_id": public_key,
        "accessToken": private_key,
        "template_params": {
            "to_email": recipient,
            "subject": f"Fresher Job Alert — {len(fresher_jobs)} roles found today!",
            "message": f"New fresher roles found:\n\n{summary}\n\nVisit your dashboard for full details.",
            "name": "FreshHire Bot",
            "email": recipient
        }
    }

    try:
        r = requests.post(
            "https://api.emailjs.com/api/v1.0/email/send",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        print(f"Email sent: {r.status_code}")
    except Exception as e:
        print(f"Email exception: {e}")

def main():
    all_jobs = []
    for company in COMPANIES:
        print(f"Scraping {company['name']}...")
        jobs = scrape_company(company)
        all_jobs.extend(jobs)
        time.sleep(1)

    output = {
        "last_updated": datetime.now().isoformat(),
        "total": len(all_jobs),
        "jobs": all_jobs
    }

    with open("jobs.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nDone! Found {len(all_jobs)} entries across {len(COMPANIES)} companies.")
    send_email(all_jobs)

if __name__ == "__main__":
    main()
