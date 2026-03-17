import json
import os
import time
from urllib.parse import unquote

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# -------------------- CONFIG --------------------
TEST_MODE = False
TEST_SCHEMES_LIMIT = 10

BASE_URL = "https://www.myscheme.gov.in/search/category/"

categories = [
    "Agriculture,Rural%20&%20Environment",
    "Banking,Financial%20Services%20and%20Insurance",
    "Business%20&%20Entrepreneurship",
    "Education%20&%20Learning",
    "Health%20&%20Wellness",
    "Housing%20&%20Shelter",
    "Public%20Safety,Law%20&%20Justice",
    "Science,IT%20&%20Communications",
    "Skills%20&%20Employment",
    "Social%20Welfare%20&%20Empowerment",
    "Sports%20&%20Culture",
    "Transport%20&%20Infrastructure",
    "Travel%20&%20Tourism",
    "Utility%20&%20Sanitation",
    "Women%20and%20Child",
]


# -------------------- PATH SETUP --------------------
def resolve_project_root() -> str:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # If this script sits inside "venv", write output to repository root.
    if os.path.basename(current_dir).lower() == "venv":
        return os.path.dirname(current_dir)
    return current_dir


PROJECT_ROOT = resolve_project_root()
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "schemes.json")

print(f"Scraper initialized. Saving data to: {OUTPUT_FILE}")


# -------------------- DRIVER --------------------
def start_driver():
    options = webdriver.ChromeOptions()
    
    # REQUIRED FOR AUTOMATION
    options.add_argument("--headless")              # Runs Chrome without a GUI
    options.add_argument("--disable-gpu")           # Applicable to windows os only
    options.add_argument("--no-sandbox")            # Bypasses OS security model
    options.add_argument("--disable-dev-shm-usage") # Overcomes limited resource problems
    
    # Optional: Set a Window Size (sometimes headless needs this to "see" elements)
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=options)
    
    # Note: maximize_window() sometimes behaves oddly in headless mode, 
    # but keeping it here is fine as a fallback.
    driver.maximize_window() 
    return driver


def safe_scroll(driver, times: int = 3):
    for _ in range(times):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)


def extract_title(driver) -> str:
    try:
        return driver.find_element(By.CSS_SELECTOR, "main h1").text.strip()
    except Exception:
        return driver.title.split("|")[0].strip()


def extract_tab_content(driver):
    sections = {
        "Details": "details",
        "Benefits": "benefits",
        "Eligibility": "eligibility",
        "Application Process": "application-process",
        "Documents Required": "documents-required",
    }
    content = {}
    for section_name, section_id in sections.items():
        try:
            section = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.ID, section_id))
            )
            section_text = section.text.strip()
            if section_text:
                content[section_name] = [section_text]
        except Exception:
            continue
    return content


def dedupe_preserve_order(urls):
    seen = set()
    unique = []
    for url in urls:
        if not url or url in seen:
            continue
        seen.add(url)
        unique.append(url)
    return unique


def run_scraper():
    driver = start_driver()
    final_data = []

    try:
        for cat_index, category in enumerate(categories):
            category_name = unquote(category).replace(",", ", ")
            print(f"\nCategory ({cat_index + 1}/{len(categories)}): {category_name}")

            category_block = {"category": category_name, "schemes": []}

            try:
                driver.get(BASE_URL + category)
                time.sleep(5)
                safe_scroll(driver, times=4)

                scheme_elements = driver.find_elements(
                    By.XPATH, "//a[contains(@href,'/schemes/')]"
                )
                raw_links = [a.get_attribute("href") for a in scheme_elements]
                scheme_links = dedupe_preserve_order(raw_links)

                if TEST_MODE:
                    scheme_links = scheme_links[:TEST_SCHEMES_LIMIT]

            except Exception as e:
                print(f"Warning: Error loading category page: {e}")
                scheme_links = []

            for i, url in enumerate(scheme_links, 1):
                print(f"   Scheme {i}/{len(scheme_links)}")
                try:
                    driver.get(url)
                    time.sleep(3)

                    closed_badge = driver.find_elements(
                        By.XPATH, "//span[normalize-space()='This scheme is closed']"
                    )
                    is_closed = len(closed_badge) > 0

                    scheme_data = {
                        "scheme_url": url,
                        "title": extract_title(driver),
                        "is_closed": is_closed,
                        "content": extract_tab_content(driver),
                    }

                    category_block["schemes"].append(scheme_data)

                except (WebDriverException, TimeoutException):
                    print("Warning: Connection issue. Skipping this scheme...")
                    continue

            final_data.append(category_block)

            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                json.dump(final_data, f, indent=4, ensure_ascii=False)

            print(f"Saved category '{category_name}' to JSON.")

    finally:
        driver.quit()
        print("\nScraping completed")


if __name__ == "__main__":
    run_scraper()
