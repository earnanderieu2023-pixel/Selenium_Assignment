import json
import os
from google import genai

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")

os.makedirs(OUTPUT_DIR, exist_ok=True)

client = genai.Client(api_key="PASTE_API_KEY_HERE")

def load_data():
    with open(os.path.join(DATA_DIR, "profile.json"), "r") as f:
        profile = json.load(f)
    with open(os.path.join(DATA_DIR, "linkedin_jobs.json"), "r") as f:
        jobs = json.load(f)
    return profile, jobs

def analyze_job(job, profile):
    prompt = f"""
You are a career advisor helping a student find the best internship match.

CANDIDATE PROFILE:
{json.dumps(profile, indent=2)}

JOB POSTING:
Title: {job['title']}
Company: {job['company']}
Location: {job['location']}
Link: {job['link']}

INSTRUCTIONS:
1. RELEVANCE CHECK: Is this a real internship/junior role suitable for a 2nd-year university student? 
   - Must be in Madrid or Remote (Stockholm is also OK)
   - Must be internship, beca, trainee, or very junior level
   - If NOT relevant, return exactly: {{"relevant": false}}

2. If relevant, return a JSON object with these exact keys:
{{
  "relevant": true,
  "fit_score": <integer 1-10>,
  "fit_summary": "<2-3 sentence summary of why this is a good or bad fit>",
  "key_gaps": ["<gap1>", "<gap2>"],
  "cv_tips": ["<specific tip to tailor CV for this role>", "<another tip>"],
  "cover_letter": "<a compelling 3-paragraph cover letter tailored to this job and candidate>"
}}

Return ONLY valid JSON, no markdown, no explanation.
"""
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    text = response.text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    text = text.strip()
    return json.loads(text)

def process_all_jobs():
    print("Loading data...")
    profile, jobs = load_data()

    # load already analyzed job ids to skip them
    json_path = os.path.join(OUTPUT_DIR, "job_leads.json")
    existing_results = []
    analyzed_ids = set()
    if os.path.exists(json_path):
        with open(json_path, "r") as f:
            existing_results = json.load(f)
            analyzed_ids = {job["job_id"] for job in existing_results}

    jobs = [job for job in jobs if job["job_id"] not in analyzed_ids]
    print(f"Analyzing {len(jobs)} new jobs ({len(analyzed_ids)} already done)")

    results = []
    skipped = 0

    for i, job in enumerate(jobs):
        print(f"[{i+1}/{len(jobs)}] {job['title']} at {job['company']}...", end=" ", flush=True)
        try:
            analysis = analyze_job(job, profile)
            if not analysis.get("relevant", False):
                print("SKIPPED (not relevant)")
                skipped += 1
                continue
            result = {**job, **analysis}
            results.append(result)
            print(f"✓ Fit score: {analysis.get('fit_score')}/10")
        except Exception as e:
            print(f"ERROR: {e}")
            continue

    all_results = existing_results + results
    all_results.sort(key=lambda x: x.get("fit_score", 0), reverse=True)

    print(f"\nDone. {len(results)} new relevant jobs found, {skipped} skipped.")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print(f"JSON saved to {json_path}")

    md_path = os.path.join(OUTPUT_DIR, "job_leads.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Job Leads Analysis\n\n")
        f.write(f"*{len(all_results)} relevant jobs found*\n\n")
        f.write("---\n\n")
        for r in all_results:
            f.write(f"## {r['fit_score']}/10 — {r['title']} at {r['company']}\n\n")
            f.write(f"**Location:** {r['location']}  \n")
            f.write(f"**Link:** {r['link']}  \n\n")
            f.write(f"### Fit Summary\n{r['fit_summary']}\n\n")
            if r.get('key_gaps'):
                f.write("### Key Gaps\n")
                for gap in r['key_gaps']:
                    f.write(f"- {gap}\n")
                f.write("\n")
            if r.get('cv_tips'):
                f.write("### CV Tips\n")
                for tip in r['cv_tips']:
                    f.write(f"- {tip}\n")
                f.write("\n")
            if r.get('cover_letter'):
                f.write(f"### Cover Letter\n{r['cover_letter']}\n\n")
            f.write("---\n\n")
    print(f"Markdown saved to {md_path}")

if __name__ == "__main__":
    process_all_jobs()
