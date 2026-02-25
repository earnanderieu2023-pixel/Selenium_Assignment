from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pickle
import os
import time
import json

BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

def load_cookies(driver, filename):
    path = os.path.join(BASE_DIR, filename)
    with open(path, "rb") as f:
        cookies = pickle.load(f)
    for cookie in cookies:
        try:
            driver.add_cookie(cookie)
        except:
            pass


def scroll_and_load(driver, existing_ids=set()):
    jobs = []
    seen_ids = set()

    # Find the scrollable jobs list by scroll height
    scroll_container = None
    for el in driver.find_elements(By.CSS_SELECTOR, "div, ul"):
        scroll_height = driver.execute_script("return arguments[0].scrollHeight", el)
        client_height = driver.execute_script("return arguments[0].clientHeight", el)
        if scroll_height > 2000 and client_height > 400:
            cls = el.get_attribute("class") or ""
            if "jobs-search__job-details" not in cls:
                scroll_container = el
                print(f"Found scroll container: {cls[:60]}")
                break

    for i in range(20):
        if scroll_container:
            driver.execute_script("arguments[0].scrollTop += 400", scroll_container)
        time.sleep(1.5)

        cards = driver.find_elements(By.CSS_SELECTOR, "li[data-occludable-job-id]")
        for card in cards:
            job_id = card.get_attribute("data-occludable-job-id")
            if not job_id or job_id in seen_ids or job_id in existing_ids:
                continue
            try:
                title = card.find_element(By.CSS_SELECTOR, "a strong").text.strip()
                company = card.find_element(By.CSS_SELECTOR, ".artdeco-entity-lockup__subtitle").text.strip()
                location = card.find_element(By.CSS_SELECTOR, ".artdeco-entity-lockup__caption").text.strip()
                link = card.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
                if title and company:
                    seen_ids.add(job_id)
                    jobs.append({
                        "title": title,
                        "company": company,
                        "location": location,
                        "link": link,
                        "job_id": job_id,
                        "source": "LinkedIn"
                    })
                    print(f"Found: {title} at {company} — {location}")
            except:
                continue

    return jobs

def scrape_page(driver, existing_ids=set()):
    return scroll_and_load(driver, existing_ids)


def scrape_linkedin():
    options = Options()
    driver = webdriver.Chrome(options=options)

    driver.get("https://www.linkedin.com")
    load_cookies(driver, "linkedin_cookies.pkl")
    driver.refresh()
    time.sleep(3)

    driver.get("https://www.linkedin.com/jobs/collections/recommended/")
    time.sleep(8)

    # Load existing job IDs to avoid duplicates
    existing_ids = set()
    output_path = os.path.join(BASE_DIR, "linkedin_jobs.json")
    if os.path.exists(output_path):
        with open(output_path, "r") as f:
            existing = json.load(f)
            existing_ids = {job["job_id"] for job in existing}
        print(f"Loaded {len(existing_ids)} existing jobs to skip")

    all_jobs = []
    page = 1

    while True:
        print(f"\n--- Scraping page {page} ---")

        jobs = scrape_page(driver, existing_ids)
        all_jobs.extend(jobs)
        print(f"Page {page}: found {len(jobs)} new jobs")

        # Try to click next page
        try:
            next_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='View next page']"))
            )
            driver.execute_script("arguments[0].click();", next_button)
            print(f"Moving to page {page + 1}")
            page += 1
            time.sleep(5)
        except:
            print("No more pages")
            break

        if page > 20:
            break

    driver.quit()
    return all_jobs

if __name__ == "__main__":
    jobs = scrape_linkedin()
    print(f"\nTotal new jobs found: {len(jobs)}")

    output_path = os.path.join(BASE_DIR, "linkedin_jobs.json")

    # Merge with existing jobs
    existing_jobs = []
    if os.path.exists(output_path):
        with open(output_path, "r") as f:
            existing_jobs = json.load(f)

    all_jobs = existing_jobs + jobs
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_jobs, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(all_jobs)} total jobs to {output_path} ({len(jobs)} new)")