from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import pickle
import os

BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

def save_session(site_name, url, filename):
    print(f"\nOpening {site_name}...")
    options = Options()
    driver = webdriver.Chrome(options=options)
    driver.get(url)

    input(f"Log in to {site_name} manually, then press Enter here when you see your feed/homepage...")

    cookies = driver.get_cookies()
    path = os.path.join(BASE_DIR, filename)
    with open(path, "wb") as f:
        pickle.dump(cookies, f)

    print(f"{site_name} session saved!")
    driver.quit()


def main():
    save_session("LinkedIn", "https://www.linkedin.com/login", "linkedin_cookies.pkl")


if __name__ == "__main__":
    main()
