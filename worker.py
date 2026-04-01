# Runs Apify, Claude and sends email every hour

import time, schedule, json, smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from apify_client import ApifyClient
import anthropic
import os
import time
from database import init_db, get_subscribers, is_new_job, mark_seen

init_db()

APIFY_TOKEN      = os.environ["APIFY_TOKEN"]
ANTHROPIC_KEY    = os.environ["ANTHROPIC_KEY"]
GMAIL_USER       = os.environ["GMAIL_USER"]
GMAIL_PASSWORD   = os.environ["GMAIL_PASSWORD"]  # Gmail App Password

SYSTEM_PROMPT = os.environ["JOB_MATCHER_PROMPT"]  

#Linked scrapper Apify called here 
def fetch_jobs(role, city):
    start = time.perf_counter()
    client = ApifyClient(APIFY_TOKEN)
    run_input = {
            
            "limit": 10,
            "locationSearch":
                [city],
           
            "timeRange": "1h",
            "titleSearch":
                [role],
            "descriptionType": "text"
        }
    run = client.actor("fantastic-jobs/advanced-linkedin-job-search-api").call(
        run_input=run_input
    )
    end = time.perf_counter()
    print(f"Time taken for Fetching Jobs from Apify: {end - start:.6f} seconds")
    return(list(client.dataset(run["defaultDatasetId"]).iterate_items()))

def match_with_claude(role, city, resume, jobs):
    start = time.perf_counter()
    print(f"Inside call to LLM")
    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content":
            f"Role: {role}\nCity: {city}\nResume:\n{resume}\n\nJobs:\n{json.dumps(jobs)}"
        }],
    )
    print(f"Response received from LLM")
    raw = response.content[0].text.strip()

    # Strip markdown fences if Claude wraps the JSON
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    # Catch truncation early with a helpful message
    if not raw.endswith("}"):
        print("⚠️ Response appears truncated. Last 200 chars:")
        print(raw[-200:])
        raise ValueError("Claude response was cut off — increase max_tokens")

    try:
        result = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"JSON parse error at: {e}")
        print(f"Problematic area:\n{raw[max(0, e.pos-100):e.pos+100]}")
        raise
   
    end = time.perf_counter()
    print(f"Time taken for Job Matching with LLM: {end - start:.6f} seconds")
    return result

def send_email(to, subject, body):
    msg = MIMEMultipart()
    msg.attach(MIMEText(body, "html"))
    msg["Subject"] = subject
    msg["From"]    = GMAIL_USER
    msg["To"]      = to
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(GMAIL_USER, GMAIL_PASSWORD)
        s.send_message(msg)

def run_for_subscriber(sub):
    print(f"Processing {sub['email']} — {sub['role']} in {sub['city']}")
    try:
        all_jobs = fetch_jobs(sub['role'], sub['city'])

        # Filter only jobs this subscriber hasn't seen
        new_jobs = [j for j in all_jobs if is_new_job(j.get("id", j.get("url", "")), sub["email"])]

        if not new_jobs:
            print(f"  No new jobs for {sub['email']}")
            return
        print(f"Job Matching call to LLM for {sub['email']} — {sub['role']} in {sub['city']}")
        result = match_with_claude(sub["role"], sub["city"], sub["resume"], new_jobs)

        # Mark all as seen
        for j in all_jobs:
            mark_seen(j.get("id", j.get("url", "")), sub["email"])
        good = [j for j in result["jobs"] if j["recommendation"] in ("Apply", "Maybe")]
        body = result.get("email_content", {}).get("html_body", "See attached jobs")
        subj = result.get("email_content", {}).get("subject", f"New {sub['role']} jobs in {sub['city']}")
        send_email(sub["email"], subj, body)
        print(subj, body);
        print(f"  Emailed {len(good)} matches to {sub['email']}")

    except Exception as e:
        print(f"  ERROR for {sub['email']}: {e}")

def hourly_run():
    print(f"\n--- Hourly run started ---")
    for sub in get_subscribers():
        run_for_subscriber(sub)
    print("--- Run complete ---\n")

# Run immediately on start, then every hour
hourly_run()
schedule.every(1).hour.do(hourly_run)

while True:
    schedule.run_pending()
    time.sleep(60)

   
