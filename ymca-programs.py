from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
from urllib.parse import urljoin
import json
import re

# Constants
YMCA_PROGRAM_SEARCH_URL = "https://www.ymcacny.org/program-search"
IFRAME_BASE_URL = "https://operations.daxko.com"

# Initialize WebDriver with error handling
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Run in headless mode (optional)
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

def create_driver():
    """Creates and returns a new WebDriver instance."""
    return webdriver.Chrome(options=options)

# Create the driver
driver = create_driver()

# Dictionary to store all categories and their activities
all_data = {}

def clean_category_name(category_text):
    """
    Cleans category name by removing numbers and extra spaces.
    Example: "Access & Ability\n                \n\n5" -> "Access & Ability"
    """
    category_text = re.sub(r"\s*\d+$", "", category_text.strip())  # Remove trailing numbers
    category_text = re.sub(r"\s+", " ", category_text).strip()  # Collapse multiple spaces
    return category_text

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
        clean_category_name(cat.text): urljoin(IFRAME_BASE_URL, cat["href"])
        for cat in soup.select("a.ga-event")
        if "/ProgramsV2/Search.mvc?category_ids=" in cat["href"]
    }

    driver.switch_to.default_content()  # Exit iframe

    for category, category_url in category_links.items():
        print(f"\nProcessing Category: {category} -> {category_url}")
        driver.get(category_url)
        time.sleep(3)  # Wait for page to load

        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Extract activities under the category
        activities = []
        for item in soup.select("li.programResults__list-item"):
            title_elem = item.find("h3")
            link_elem = item.find("a", class_="ga-event")
            date_elem = item.select_one("div.programResults__date-details div.pull-left")

            if title_elem and link_elem:
                activity_title = title_elem.text.strip()
                activity_url = urljoin(IFRAME_BASE_URL, link_elem["href"])
                activity_date = date_elem.text.strip() if date_elem else "No date found"

                activities.append({
                    "title": activity_title,
                    "url": activity_url,
                    "date": activity_date
                })

        # Store category data
        all_data[category] = activities

        # Visit each activity page for full details
        for activity in activities:
            print(f"  - Fetching details for: {activity['title']} -> {activity['url']}")

            try:
                driver.get(activity["url"])
                time.sleep(3)  # Allow time for JavaScript to render
                activity_soup = BeautifulSoup(driver.page_source, "html.parser")

                # Extract description from <meta property="og:description">
                description_elem = activity_soup.find("meta", {"property": "og:description"})
                description = description_elem.get("content", "No description found").strip()

                # Extract location from data-enh-ec-location attribute
                location_elem = activity_soup.find(attrs={"data-enh-ec-location": True})
                location = location_elem.get("data-enh-ec-location", "No location found").strip()

                # Update activity details
                activity["description"] = description
                activity["location"] = location
                activity["category"] = category  # Include category for reference

            except Exception as e:
                print(f"Error fetching details for {activity['title']}: {str(e)}")
                continue  # Skip this activity if an error occurs

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
