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
        "id_patterns": [],
    },
}

def extract_pixel_id(script_text, id_patterns):
    """Extracts pixel/tracking ID from script text using regex patterns."""
    if not script_text:
        return None

    for pattern in id_patterns:
        match = re.search(pattern, script_text)
        if match and match.groups():
            return match.group(1)  # ✅ Extract the first found ID

    return None

def extract_shopify_pixels(soup):
    """Extracts tracking pixels from Shopify's Web Pixels Manager JSON."""
    for script in soup.find_all("script"):
        script_content = script.string
        if script_content and "webPixelsConfigList" in script_content:
            try:
                # ✅ Extract JSON-like structure from the script content
                json_match = re.search(r"webPixelsConfigList\":(\[.*?\])", script_content)
                if json_match:
                    json_data = json.loads(json_match.group(1))  # ✅ Convert to Python dict
                    
                    # ✅ Extract tracking pixels from JSON
                    extracted_pixels = {}
                    for entry in json_data:
                        if "configuration" in entry:
                            config = json.loads(entry["configuration"])
                            if "pixel_id" in config:
                                extracted_pixels[entry["id"]] = {
                                    "found": True,
                                    "pixel_id": config["pixel_id"]
                                }

                    return extracted_pixels  # ✅ Return extracted tracking pixels

            except json.JSONDecodeError:
                pass  # ✅ Continue if JSON parsing fails

    return {}  # ✅ Return empty dictionary if no pixels found

def check_tracking_pixels(url):
    """Scans a website for tracking pixels and extracts IDs if found"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        found_pixels = {}

        # ✅ Extract standard tracking pixels
        for name, data in TRACKING_PATTERNS.items():
            identifier = data["identifier"]
            id_patterns = data["id_patterns"]
            pixel_id = None

            # ✅ Check <script> tags for tracking pixels
            for script in soup.find_all("script"):
                script_content = script.string
                if script_content and identifier in script_content:
                    pixel_id = extract_pixel_id(script_content, id_patterns)
                    break  # Stop after finding the first valid match

            found_pixels[name] = {
                "found": bool(pixel_id),
                "pixel_id": pixel_id
            }

        # ✅ Extract Shopify-specific tracking pixels
        shopify_pixels = extract_shopify_pixels(soup)
        found_pixels.update(shopify_pixels)  # ✅ Merge results with standard tracking pixels

        return {"url": url, "tracking_pixels": found_pixels}

    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to fetch {url}: {e}"}

# Example usage
if __name__ == "__main__":
    url = input("Enter website URL: ")
    result = check_tracking_pixels(url)
    print(result)
