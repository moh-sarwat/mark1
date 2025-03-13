import requests
from bs4 import BeautifulSoup
import time

from scan_pixels import check_tracking_pixels

def get_site_links(url):
    """Extracts all internal links from the given URL"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        links = set()
        for link in soup.find_all("a", href=True):
            full_link = requests.compat.urljoin(url, link["href"])
            if url in full_link:  # Ensure it's an internal link
                links.add(full_link)

        return list(links)[:10]  # ✅ LIMIT TO 10 PAGES TO AVOID CRASHES

    except requests.exceptions.RequestException as e:
        return []

def scan_full_site(url):
    """Scans the homepage and up to 10 internal pages for tracking pixels"""
    all_results = {}

    pages_to_scan = get_site_links(url)
    pages_to_scan.insert(0, url)  # ✅ Ensure the main page is scanned first

    print(f"Scanning {len(pages_to_scan)} pages...")

    for page in pages_to_scan:
        try:
            # ✅ ADD DELAY TO REDUCE MEMORY USAGE
            time.sleep(1)

            scan_result = check_tracking_pixels(page)
            all_results[page] = scan_result["tracking_pixels"]

        except Exception as e:
            all_results[page] = {"error": str(e)}

    return {"tracking_pixels": merge_results(all_results)}

def merge_results(all_results):
    """Merges results from all pages to avoid duplicate pixel detection"""
    merged = {}

    for page, scan in all_results.items():
        for pixel, details in scan.items():
            if pixel not in merged:
                merged[pixel] = {"found": False, "pixel_id": None, "pages_found": []}

            if details["found"]:
                merged[pixel]["found"] = True
                merged[pixel]["pixel_id"] = details["pixel_id"]
                merged[pixel]["pages_found"].append(page)

    return merged
