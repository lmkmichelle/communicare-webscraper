from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import json
from urllib.parse import urljoin

# Base URL for YMCA Ithaca Events
YMCA_EVENTS_URL = "https://www.ithacaymca.com/events/"
BASE_URL = "https://www.ithacaymca.com"

# Initialize WebDriver
driver = webdriver.Chrome()

all_events = []

try:
    print(f"Scraping main YMCA Events Page: {YMCA_EVENTS_URL}")
    driver.get(YMCA_EVENTS_URL)

    # Wait for events to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.event-item"))
    )

    # Parse events list
    soup = BeautifulSoup(driver.page_source, "html.parser")
    event_items = soup.select("div.event-item")

    for event in event_items:
        title_elem = event.find("a", class_="event-more-link")
        date_elem = event.find("h4")
        time_elem = event.find("p", class_="event time small-4 columns")

        if title_elem and date_elem:
            event_title = title_elem.text.strip()
            event_url = urljoin(BASE_URL, title_elem["href"])
            event_date = date_elem.text.strip()
            event_time = time_elem.text.strip() if time_elem else "No time listed"

            event_details = {
                "title": event_title,
                "date": event_date,
                "time": event_time,
                "url": event_url,
            }

            all_events.append(event_details)

    # Visit each event page for full details
    for event in all_events:
        print(f"Fetching details for: {event['title']} -> {event['url']}")
        driver.get(event["url"])
        time.sleep(3)

        event_soup = BeautifulSoup(driver.page_source, "html.parser")

        # Extract all text from the event page
        all_text = " ".join([p.text.strip() for p in event_soup.find_all("p")])

        # Store full event details
        event["full_description"] = all_text

finally:
    driver.quit()

# Save to JSON
with open("ymca_events.json", "w", encoding="utf-8") as f:
    json.dump(all_events, f, indent=4)

# Print structured output
for event in all_events:
    print(f"\nEvent: {event['title']}")
    print(f"  Date: {event['date']}")
    print(f"  Time: {event['time']}")
    print(f"  URL: {event['url']}")
    print(f"  Full Description: {event['full_description'][:300]}...")  # Print first 300 chars
