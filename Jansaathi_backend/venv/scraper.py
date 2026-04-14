import time
import json
import os
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, InvalidSessionIdException

# -------------------- CONFIG --------------------
TEST_MODE = False
TEST_SCHEMES_LIMIT = 10 
BASE_URL = "https://www.myscheme.gov.in/search/category/"

CATEGORIES_MAP = {
    "Agriculture,Rural%20&%20Environment": "Agriculture, Rural & Environment",
    "Banking,Financial%20Services%20and%20Insurance": "Banking, Financial Services and Insurance",
    "Business%20&%20Entrepreneurship": "Business & Entrepreneurship",
    "Education%20&%20Learning": "Education & Learning",
    "Health%20&%20Wellness": "Health & Wellness",
    "Housing%20&%20Shelter": "Housing & Shelter",
    "Public%20Safety,Law%20&%20Justice": "Public Safety, Law & Justice",
    "Science,IT%20&%20Communications": "Science, IT & Communications",
    "Skills%20&%20Employment": "Skills & Employment",
    "Social%20Welfare%20&%20Empowerment": "Social Welfare & Empowerment",
    "Sports%20&%20Culture": "Sports & Culture",
    "Transport%20&%20Infrastructure": "Transport & Infrastructure",
    "Travel%20&%20Tourism": "Travel & Tourism",
    "Utility%20&%20Sanitation": "Utility & Sanitation",
    "Women%20and%20Child": "Women and Child"
}

# -------------------- PATH SETUP --------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
os.makedirs(DATA_DIR, exist_ok=True)
OUTPUT_FILE = os.path.join(DATA_DIR, "schemes.json")

# -------------------- DRIVER UTILS --------------------
def start_driver():
    """Initializes Chrome with stability flags."""
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--remote-debugging-port=9222")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    try:
        driver = webdriver.Chrome(options=options)
        driver.maximize_window()
        return driver
    except Exception as e:
        print(f"❌ Driver startup failed: {e}. Retrying in 5s...")
        time.sleep(5)
        return webdriver.Chrome(options=options)

def safe_scroll(driver, times=3):
    """Scrolls with error handling for disconnected sessions."""
    try:
        for _ in range(times):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1.5)
    except Exception:
        print("⚠️ Scroll interrupted (session might be lost).")

def extract_tab_content(driver):
    sections = {
        "Details": "details",
        "Benefits": "benefits",
        "Eligibility": "eligibility",
        "Application Process": "application-process",
        "Documents Required": "documents-required"
    }
    content = {}
    for section_name, section_id in sections.items():
        try:
            # Short wait for SPA content to render
            section = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.ID, section_id))
            )
            text = section.text.strip()
            if text:
                content[section_name] = [text]
        except:
            continue
    return content

# -------------------- MAIN SCRAPER --------------------
driver = start_driver()
final_data = []

# Resume logic: Load existing progress
if os.path.exists(OUTPUT_FILE):
    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        try:
            final_data = json.load(f)
        except:
            final_data = []

for cat_index, (slug, category_name) in enumerate(CATEGORIES_MAP.items()):
    print(f"\n📂 CATEGORY ({cat_index+1}/{len(CATEGORIES_MAP)}): {category_name}")
    
    # Check if category is already processed
    if any(item.get('category') == category_name for item in final_data):
        print(f"⏩ Skipping {category_name} (Already scraped).")
        continue

    category_block = {"category": category_name, "schemes": []}
    
    try:
        driver.get(BASE_URL + slug)
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(5) # Allow JS to load cards
        safe_scroll(driver, times=4)

        scheme_elements = driver.find_elements(By.CSS_SELECTOR, "a[href*='/schemes/']")
        scheme_links = list({a.get_attribute("href") for a in scheme_elements if "/schemes/" in a.get_attribute("href")})
        
        if TEST_MODE:
            scheme_links = scheme_links[:TEST_SCHEMES_LIMIT]
            
        print(f"🔍 Found {len(scheme_links)} schemes.")

        for i, url in enumerate(scheme_links, 1):
            print(f"   🔹 Scheme {i}/{len(scheme_links)}")
            
            # INNER RETRY LOOP FOR SESSION CRASHES
            for retry in range(2):
                try:
                    driver.get(url)
                    time.sleep(3)
                    
                    title = driver.title.split("|")[0].strip()
                    try:
                        title = driver.find_element(By.CSS_SELECTOR, "main h1").text.strip()
                    except: pass

                    closed_badge = driver.find_elements(By.XPATH, "//*[contains(text(), 'This scheme is closed')]")
                    
                    scheme_data = {
                        "scheme_url": url,
                        "title": title,
                        "is_closed": len(closed_badge) > 0,
                        "content": extract_tab_content(driver)
                    }
                    category_block["schemes"].append(scheme_data)
                    break # Success, exit retry loop
                    
                except (InvalidSessionIdException, WebDriverException):
                    print("⚠️ Browser crashed. Attempting to restart driver...")
                    try: driver.quit() 
                    except: pass
                    time.sleep(3)
                    driver = start_driver()
                    # Retry the same URL once

        # Save category block
        final_data.append(category_block)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(final_data, f, indent=4, ensure_ascii=False)
        print(f"✅ Successfully saved {category_name}")

    except Exception as e:
        print(f"❌ Fatal error in category {category_name}: {e}")
        # Restart driver for the next category
        try: driver.quit()
        except: pass
        driver = start_driver()

driver.quit()
print("\n🎉 ALL CATEGORIES SCRAPED SUCCESSFULLY.")