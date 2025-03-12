import requests
from bs4 import BeautifulSoup
import re

# Define tracking pixel identifiers & ID extraction patterns
TRACKING_PATTERNS = {
    "Meta Pixel": {"identifier": "connect.facebook.net", "id_pattern": "fbq('init', '"},
    "Google Analytics (GA4)": {"identifier": "gtag('config'", "id_pattern": "gtag('config', '"},
    "Google Analytics (Universal)": {"identifier": "analytics.js", "id_pattern": "ga('create', '"},
    "Google Tag Manager": {"identifier": "googletagmanager.com", "id_pattern": "GTM-"},
    "TikTok Pixel": {"identifier": "analytics.tiktok.com", "id_pattern": "ttq.identify("},
    "Snapchat Pixel": {"identifier": "sc-static.net/s", "id_pattern": "snaptr('init', '"},
    "LinkedIn Insight": {"identifier": "linkedin.com/insightTag", "id_pattern": None},
    "Microsoft Clarity": {"identifier": "clarity.ms", "id_pattern": None},
    "Pinterest Tag": {"identifier": "ct.pinterest.com", "id_pattern": None},
    "Twitter (X) Pixel": {"identifier": "ads.twitter.com", "id_pattern": None}
}

# Regex patterns for better ID extraction
PIXEL_REGEX_PATTERNS = {
    "Meta Pixel": r"fbq\('init',\s*['\"]?([\d]+)['\"]?\)|window\.fbqQueue\s*=\s*\[.*?['\"]?([\d]+)['\"]?",
    "Google Analytics (GA4)": r"gtag\('config',\s*['\"]?([A-Z0-9\-]+)['\"]?\)",
    "Google Analytics (Universal)": r"ga\('create',\s*['\"]?([A-Z0-9\-]+)['\"]?\)",
    "Google Tag Manager": r"GTM-[A-Z0-9]+",
    "TikTok Pixel": r"ttq.identify\(\"([\d]+)\"\)",
    "LinkedIn Insight": r"linkedin.com/insightTag/([\d]+)",
    "Snapchat Pixel": r"snaptr\('init',\s*['\"]?([A-Z0-9\-]+)['\"]?\)|window\.snaptr\s*=\s*\{.*?['\"]?([A-Z0-9\-]+)['\"]?"
}

def extract_pixel_id(script_text, id_pattern, pixel_name):
    """ Extracts pixel/tracking ID from script text using regex patterns """
    if not script_text:
        return None

    try:
        # Generic method: Find the pixel ID after the given pattern
        if id_pattern and id_pattern in script_text:
            return script_text.split(id_pattern)[1].split("'")[0]

        # Regex-based extraction for more complex tracking IDs
        if pixel_name in PIXEL_REGEX_PATTERNS:
            match = re.search(PIXEL_REGEX_PATTERNS[pixel_name], script_text)
            if match:
                return match.group(1)  # Extract the first capture group as the ID

    except Exception as e:
        print(f"Error extracting ID for {pixel_name}: {e}")

    return None

def extract_meta_pixel_id(soup, script_text):
    """ Extract Meta Pixel ID from multiple sources: JavaScript, JSON, or HTML attributes """
    # Method 1: Standard `fbq('init', '1234567890')`
    match = re.search(r"fbq\('init',\s*['\"]?([\d]+)['\"]?\)", script_text)
    if match:
        return match.group(1)

    # Method 2: JSON-based Meta Pixel inside `window.fbqQueue`
    match = re.search(r"window\.fbqQueue\s*=\s*\[.*?['\"]?([\d]+)['\"]?", script_text)
    if match:
        return match.group(1)

    # Method 3: Check for `<meta>` tags or `data-meta-pixel-id` attributes
    meta_tag = soup.find("meta", {"data-meta-pixel-id": True})
    if meta_tag:
        return meta_tag["data-meta-pixel-id"]

    return None

def check_tracking_pixels(url):
    """ Scans a website for tracking pixels and extracts IDs if found """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        found_pixels = {}
        for name, data in TRACKING_PATTERNS.items():
            identifier = data["identifier"]
            id_pattern = data["id_pattern"]
            pixel_id = None

            for script in soup.find_all("script"):
                if script.string and identifier in script.string:
                    pixel_id = extract_pixel_id(script.string, id_pattern, name)
                    break  # Stop once we find the first valid match

            # Special case: Meta Pixel (extract from multiple sources)
            if name == "Meta Pixel" and not pixel_id:
                pixel_id = extract_meta_pixel_id(soup, script.string)

            found_pixels[name] = {
                "found": bool(pixel_id or identifier in str(soup)),
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
