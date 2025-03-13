import requests
from bs4 import BeautifulSoup
import time
from urllib.parse import urljoin, urlparse

from scan_pixels import check_tracking_pixels

def extract_internal_links(base_url, max_pages=10):
    """Extracts internal links from the homepage, limiting the number of pages scanned."""
    try:
        response = requests.get(base_url, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        links = set()
        for link in soup.find_all("a", href=True):
            full_url = urljoin(base_url, link["href"])
            parsed_url = urlparse(full_url)

            # ✅ Ensure it's an internal link & not a file (e.g., PDF, image, video)
            if parsed_url.netloc == urlparse(base_url).netloc and not full_url.endswith((".pdf", ".jpg", ".png", ".mp4", ".zip")):
                links.add(full_url)

        return list(links)[:max_pages]  # ✅ LIMIT to `max_pages` (e.g., 10)
    
    except requests.exceptions.RequestException:
        return []

def scan_full_site(url):
    """Scans the homepage and a limited number of internal pages for tracking pixels."""
    pages_to_scan = extract_internal_links(url)
    pages_to_scan.insert(0, url)  # ✅ Ensure homepage is scanned first

    print(f"🔍 Scanning {len(pages_to_scan)} pages...")

    all_results = {}

    for page in pages_to_scan:
        try:
            # ✅ ADD SMALL DELAY TO AVOID MEMORY SPIKES
            time.sleep(1)

            scan_result = check_tracking_pixels(page)
            all_results[page] = scan_result["tracking_pixels"]

        except Exception as e:
            all_results[page] = {"error": str(e)}

    return {"tracking_pixels": merge_results(all_results)}

def merge_results(all_results):
    """Merges tracking pixel results across multiple pages."""
    merged = {}

    for page, scan in all_results.items():
        for pixel, details in scan.items():
            if pixel not in merged:
                merged[pixel] = {"found": False, "pixel_id": None, "pages_found": []}

            if details["found"]:
                merged[pixel]["found"] = True
                if details["pixel_id"]:
                    merged[pixel]["pixel_id"] = details["pixel_id"]
                merged[pixel]["pages_found"].append(page)

    return merged
