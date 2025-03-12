import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from scan_pixels import check_tracking_pixels

def extract_internal_links(base_url):
    """Extracts all internal links from the homepage"""
    try:
        response = requests.get(base_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        links = set()
        for link in soup.find_all("a", href=True):
            href = link["href"]
            full_url = urljoin(base_url, href)

            # Ensure it's an internal link
            if urlparse(full_url).netloc == urlparse(base_url).netloc:
                links.add(full_url)

        return list(links)
    except Exception as e:
        print(f"Error extracting links: {e}")
        return []

def scan_full_site(url):
    """Scans all internal pages of a website and aggregates tracking pixel results."""
    crawled_pages = extract_internal_links(url)
    crawled_pages.insert(0, url)  # Ensure homepage is included

    print(f"Scanning {len(crawled_pages)} pages...")

    pages_results = {}

    for page in crawled_pages:
        try:
            scan_result = check_tracking_pixels(page)
            pages_results[page] = scan_result["tracking_pixels"]
        except Exception as e:
            pages_results[page] = {"error": str(e)}

    # ✅ Debugging: Print pages_results to see what's wrong
    print("DEBUG: Full Scan Output:")
    print(pages_results)

    # ✅ Aggregate results properly
    summary = {}

    for page, pixels in pages_results.items():
        if isinstance(pixels, str):  # ✅ Fix potential error
            print(f"Skipping {page} due to error: {pixels}")
            continue  # Skip if response is not valid

        for pixel, data in pixels.items():
            if pixel not in summary:
                summary[pixel] = {"found": False, "pixel_id": None, "pages_found": []}

            if isinstance(data, dict) and "found" in data:  # ✅ Ensure data is valid
                if data["found"]:
                    summary[pixel]["found"] = True
                    summary[pixel]["pages_found"].append(page)
                    if data["pixel_id"] and summary[pixel]["pixel_id"] is None:
                        summary[pixel]["pixel_id"] = data["pixel_id"]

    return {"tracking_pixels": summary}
