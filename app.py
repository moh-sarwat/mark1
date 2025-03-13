import os
from flask import Flask, request, jsonify
from scan_pixels import check_tracking_pixels
from crawl_and_scan import scan_full_site

app = Flask(__name__)

@app.route("/")
def home():
    return "Tracking Scanner is Running!"

@app.route("/scan", methods=["GET"])
def scan():
    """Handles scanning requests for tracking pixels."""
    url = request.args.get("url")
    crawl = request.args.get("crawl", "false").lower() == "true"

    if not url:
        return jsonify({"error": "Missing 'url' parameter"}), 400

    if crawl:
        result = scan_full_site(url)  # Full crawl mode
    else:
        result = check_tracking_pixels(url)  # Single-page mode

    return jsonify(result)

# Use Railway’s dynamic PORT environment variable
# if __name__ == "__main__":
#    port = int(os.environ.get("PORT", 5000))
#    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
