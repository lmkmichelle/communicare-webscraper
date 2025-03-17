from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
from urllib.parse import urljoin
import json

YMCA_PROGRAM_SEARCH_URL = "https://www.ymcacny.org/program-search"
IFRAME_BASE_URL = "https://operations.daxko.com"

driver = webdriver.Chrome()

all_data = {}

try:
    print(f"Scraping main YMCA Program Search Page: {YMCA_PROGRAM_SEARCH_URL}")
    driver.get(YMCA_PROGRAM_SEARCH_URL)

    # Wait for iframe to load
    iframe = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "daxko_iframe"))
    )
    driver.switch_to.frame(iframe)

    # Wait for categories to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "a.ga-event"))
    )

    # Parse categories
    soup = BeautifulSoup(driver.page_source, "html.parser")
    category_links = {
        cat.text.strip(): urljoin(IFRAME_BASE_URL, cat["href"])
        for cat in soup.select("a.ga-event")
        if "/ProgramsV2/Search.mvc?category_ids=" in cat["href"]
    }

    driver.switch_to.default_content() 

    # Visit each category's Daxko page
    for category, category_url in category_links.items():
        print(f"\nProcessing Category: {category} -> {category_url}")
        driver.get(category_url)

        time.sleep(3)  
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Extract activities under the category
        activities = []
        for item in soup.select("li.programResults__list-item"):
            title_elem = item.find("h3")
            link_elem = item.find("a", class_="ga-event")
            date_elem = item.select_one("div.programResults__date-details div.pull-left")
            location_elem = item.select_one("div.programResults__list-item div:nth-of-type(2)")

            if title_elem and link_elem:
                activity_title = title_elem.text.strip()
                activity_url = urljoin(IFRAME_BASE_URL, link_elem["href"])
                activity_date = date_elem.text.strip() if date_elem else "No date found"
                activity_location = location_elem.text.strip() if location_elem else "No location found"

                activities.append({
                    "title": activity_title,
                    "url": activity_url,
                    "date": activity_date,
                    "location": activity_location
                })

        all_data[category] = activities

        # Visit each activity page for full details
        for activity in activities:
            print(f"  - Fetching details for: {activity['title']} -> {activity['url']}")
            driver.get(activity["url"])
            time.sleep(3) 

            activity_soup = BeautifulSoup(driver.page_source, "html.parser")

            description_elem = activity_soup.select_one("div.program-description")
            description = description_elem.text.strip() if description_elem else "No description found"

            # Update activity details
            activity["description"] = description
            activity["source_url"] = activity["url"]
            activity["category"] = category 

finally:
    driver.quit()

# Save to JSON
with open("ymca_programs.json", "w", encoding="utf-8") as f:
    json.dump(all_data, f, indent=4)

# Print structured output
for category, activities in all_data.items():
    print(f"\nCategory: {category}")
    for activity in activities:
        print(f"  - {activity['title']} ({activity['url']})")
        print(f"    Date: {activity['date']}")
        print(f"    Location: {activity['location']}")
        print(f"    Description: {activity['description']}")
        print(f"    Source: {activity['source_url']}")
