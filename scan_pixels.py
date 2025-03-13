import requests
from bs4 import BeautifulSoup
import re
import json

# Define tracking pixel identifiers & ID extraction patterns
TRACKING_PATTERNS = {
    "Meta Pixel": {
        "identifier": "connect.facebook.net",
        "id_patterns": [
            r"fbq\(\s*['\"]init['\"]\s*,\s*['\"]?([\d]+)['\"]?\)",  # ✅ Standard fbq("init", "1234567890")
            r"facebook\.com/tr/\?id=([\d]+)",  # ✅ Matches tracking request
            r"data-fbp=['\"]?([\d]+)['\"]?",  # ✅ Matches hidden Meta Pixel in attributes
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
    "TikTok Pixel": {
        "identifier": "analytics.tiktok.com",
        "id_patterns": [r"ttq.identify\(\"([\d]+)\"\)"],
    },
    "Snapchat Pixel": {
        "identifier": "sc-static.net/s",
        "id_patterns": [r"snaptr\('init',\s*['\"]?([A-Z0-9\-]+)['\"]?\)"],
    },
    "LinkedIn Insight": {
        "identifier": "linkedin.com/insightTag",
        "id_patterns": [r"linkedin.com/insightTag/([\d]+)"],
    },
    "Shopify Web Pixels Manager": {  # ✅ NEW: Shopify tracking detection
        "identifier": "web-pixels-manager-setup",
        "id_patterns": [
            r'\"pixel_id\":\"([\d]+)\"',  # ✅ Extracts Pixel IDs from JSON inside scripts
            r'\"pixelId\":\"([\w-]+)\"',  # ✅ Matches Shopify's alternative pixel ID format
            r'\"config\":\"{\\\"pixel_id\\\":\\\"([\w-]+)\\\"',  # ✅ Extracts from Shopify GA4 setup
        ],
    },
}

def extract_pixel_id(script_text, id_patterns):
    """ Extracts pixel/tracking ID from script text using regex patterns."""
    if not script_text:
        return None

    for pattern in id_patterns:
        match = re.search(pattern, script_text)
        if match and match.groups():
            return match.group(1)  # ✅ Extract the first found ID

    return None

def check_tracking_pixels(url):
    """Scans a website for tracking pixels and extracts IDs if found"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        found_pixels = {}

        for name, data in TRACKING_PATTERNS.items():
            identifier = data["identifier"]
            id_patterns = data["id_patterns"]
            pixel_id = None

            # ✅ Check <script> tags for tracking pixels
            for script in soup.find_all("script"):
                script_content = script.string

                # ✅ Handle JSON-encoded tracking scripts (Shopify Web Pixels Manager)
                if script_content and "pixel_id" in script_content:
                    try:
                        json_data = json.loads(script_content)
                        if isinstance(json_data, dict) and "pixel_id" in json_data:
                            pixel_id = json_data["pixel_id"]
                            break  # ✅ Found Shopify tracking ID
                    except json.JSONDecodeError:
                        pass  # Continue scanning if JSON parsing fails

                # ✅ Check regular tracking scripts
                if script_content and identifier in script_content:
                    pixel_id = extract_pixel_id(script_content, id_patterns)
                    break  # Stop after finding the first valid match

            found_pixels[name] = {
                "found": bool(pixel_id),
                "pixel_id": pixel_id
            }

        return {"url": url, "tracking_pixels": found_pixels}

    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to fetch {url}: {e}"}

# Example usage
if __name__ == "__main__":
    url = input("Enter website URL: ")
    result = check_tracking_pixels(url)
    print(result)
