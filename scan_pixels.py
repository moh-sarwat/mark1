import requests
from bs4 import BeautifulSoup
import re
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

# Define tracking pixel identifiers & ID extraction patterns
TRACKING_PATTERNS = {
    "Meta Pixel": {
        "identifier": "connect.facebook.net",
        "id_patterns": [
            r"fbq\(\s*['\"]init['\"]\s*,\s*['\"]?([\d]+)['\"]?\)",  # ✅ Standard fbq("init", "1234567890")
            r"facebook\.com/tr/\?id=([\d]+)",  # ✅ Matches tracking request
        ],
    },
    "Google Analytics (GA4)": {
        "identifier": "gtag('config'",
        "id_patterns": [r"gtag\('config',\s*['\"]?([A-Z0-9\-]+)['\"]?\)"],
    },
    "Google Tag Manager": {
        "identifier": "googletagmanager.com",
        "id_patterns": [r"GTM-[A-Z0-9]+"],
    },
    "Shopify Web Pixels Manager": {
        "identifier": "webPixelsConfigList",
        "id_patterns": [],
    },
}

def setup_selenium():
    """Sets up a headless Chrome Selenium driver."""
    options = Options()
    options.add_argument("--headless")  # ✅ Run without UI
    options.add_argument("--no-sandbox")  
    options.add_argument("--disable-dev-shm-usage")  

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def extract_pixel_id(script_text, id_patterns):
    """ Extracts pixel/tracking ID from script text using regex patterns."""
    if not script_text:
        return None

    for pattern in id_patterns:
        match = re.search(pattern, script_text)
        if match and match.groups():
            return match.group(1)  # ✅ Extract the first found ID

    return None

def extract_shopify_pixels(html_source):
    """Extracts Shopify tracking pixels from Web Pixels Manager JSON."""
    shopify_pixels = {}

    try:
        json_match = re.search(r"webPixelsConfigList\":(\[.*?\])", html_source)
        if json_match:
            json_data = json.loads(json_match.group(1))  # ✅ Convert JSON to Python dict
            
            for entry in json_data:
                if "configuration" in entry:
                    config = json.loads(entry["configuration"])
                    if "pixel_id" in config:
                        shopify_pixels[entry["id"]] = {
                            "found": True,
                            "pixel_id": config["pixel_id"]
                        }
    except json.JSONDecodeError:
        pass  # ✅ Continue if JSON parsing fails

    return shopify_pixels  # ✅ Returns Shopify pixels if found

def check_tracking_pixels(url):
    """Scans a website for tracking pixels and extracts IDs using Selenium."""
    try:
        driver = setup_selenium()
        driver.get(url)
        time.sleep(5)  # ✅ Allow time for JavaScript to execute

        html_source = driver.page_source  # ✅ Get fully rendered HTML
        driver.quit()

        soup = BeautifulSoup(html_source, 'html.parser')

        found_pixels = {}

        # ✅ Extract standard tracking pixels
        for name, data in TRACKING_PATTERNS.items():
            identifier = data["identifier"]
            id_patterns = data["id_patterns"]
            pixel_id = None

            for script in soup.find_all("script"):
                script_content = script.string
                if script_content and identifier in script_content:
                    pixel_id = extract_pixel_id(script_content, id_patterns)
                    break  # ✅ Stop once found

            found_pixels[name] = {
                "found": bool(pixel_id),
                "pixel_id": pixel_id
            }

        # ✅ Extract Shopify-specific tracking pixels
        shopify_pixels = extract_shopify_pixels(html_source)
        found_pixels.update(shopify_pixels)

        return {"url": url, "tracking_pixels": found_pixels}

    except Exception as e:
        return {"error": f"Failed to scan {url}: {e}"}

# Example usage
if __name__ == "__main__":
    url = input("Enter website URL: ")
    result = check_tracking_pixels(url)
    print(result)
