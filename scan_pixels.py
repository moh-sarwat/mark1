import requests
from bs4 import BeautifulSoup
import re

# Define tracking pixel identifiers & ID extraction patterns
TRACKING_PATTERNS = {
    "Meta Pixel": {
        "identifier": "connect.facebook.net",
        "id_patterns": [
            r"fbq\(\s*['\"]init['\"]\s*,\s*['\"]?([\d]+)['\"]?\)",  # ✅ Standard fbq("init", "1234567890")
            r"facebook\.com/tr/\?id=([\d]+)",  # ✅ Matches network request pattern
            r"data-fbp=['\"]?([\d]+)['\"]?",  # ✅ Matches hidden Meta Pixel in data attributes
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

            # ✅ Check <script> tags for Pixel ID
            for script in soup.find_all("script"):
                if script.string and identifier in script.string:
                    pixel_id = extract_pixel_id(script.string, id_patterns)
                    break  # Stop once we find the first valid match

            # ✅ Check <meta> and <link> tags for hidden pixel IDs
            for meta in soup.find_all("meta"):
                meta_content = str(meta)
                if identifier in meta_content:
                    pixel_id = extract_pixel_id(meta_content, id_patterns)
                    break

            for link in soup.find_all("link"):
                link_content = str(link)
                if identifier in link_content:
                    pixel_id = extract_pixel_id(link_content, id_patterns)
                    break

            # ✅ NEW: Check <img> tags for tracking pixel
            for img in soup.find_all("img"):
                img_src = img.get("src", "")
                match = re.search(r"facebook\.com/tr\?id=([\d]+)", img_src)
                if match:
                    pixel_id = match.group(1)
                    break

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
