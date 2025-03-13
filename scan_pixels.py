import requests
from bs4 import BeautifulSoup
import re

# Define tracking pixel identifiers & ID extraction patterns
TRACKING_PATTERNS = {
    "Meta Pixel": {"identifier": "connect.facebook.net", "id_patterns": [
        r"fbq\(\s*'init'\s*,\s*['\"]?([\d]+)['\"]?\)",  # ✅ Standard fbq('init', '1234567890')
        r"facebook\.com/tr/\?id=([\d]+)",  # ✅ Network request pattern
        r"data-fbp=['\"]?([\d]+)['\"]?"  # ✅ Meta Pixel inside data attribute
    ]},
    "Google Analytics (GA4)": {"identifier": "gtag('config'", "id_patterns": [r"gtag\('config',\s*['\"]?([A-Z0-9\-]+)['\"]?\)"]},
    "Google Tag Manager": {"identifier": "googletagmanager.com", "id_patterns": [r"GTM-[A-Z0-9]+"]},
    "TikTok Pixel": {"identifier": "analytics.tiktok.com", "id_patterns": [r"ttq.identify\(\"([\d]+)\"\)"]},
    "Snapchat Pixel": {"identifier": "sc-static.net/s", "id_patterns": [r"snaptr\('init',\s*['\"]?([A-Z0-9\-]+)['\"]?\)"]},
    "LinkedIn Insight": {"identifier": "linkedin.com/insightTag", "id_patterns": [r"linkedin.com/insightTag/([\d]+)"]},
    "Microsoft Clarity": {"identifier": "clarity.ms", "id_patterns": []},
    "Pinterest Tag": {"identifier": "ct.pinterest.com", "id_patterns": []},
    "Twitter (X) Pixel": {"identifier": "ads.twitter.com", "id_patterns": []}
}

def extract_pixel_id(script_text, id_patterns):
    """Extracts pixel/tracking ID from script text using regex patterns."""
    if not script_text:
        return None

    for pattern in id_patterns:
        match = re.search(pattern, script_text)
        if match:
            return match.group(1) if match.groups() else None  # ✅ SAFE FIX: Check if group exists

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
            id_patterns = data["id_patterns"]
            pixel_id = None

            for script in soup.find_all("script"):
                if script.string and identifier in script.string:
                    pixel_id = extract_pixel_id(script.string, id_patterns)
                    break  # Stop once we find the first valid match

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
