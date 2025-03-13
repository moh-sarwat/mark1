from flask import Flask, render_template, request, send_file
from scan_pixels import check_tracking_pixels
from crawl_and_scan import scan_full_site
import pandas as pd
from weasyprint import HTML
import os

app = Flask(__name__)

# Store last scan results
last_scan = {}

@app.route("/", methods=["GET", "POST"])
def home():
    global last_scan

    if request.method == "POST":
        url = request.form.get("url")
        crawl = request.form.get("crawl") == "true"

        if crawl:
            scan_result = scan_full_site(url)  # Full-site scan
        else:
            scan_result = check_tracking_pixels(url)  # Quick scan

        # ✅ Store the last scan results
        last_scan = {
            "url": url,
            "crawl": crawl,
            "data": scan_result["tracking_pixels"]
        }

        return render_template("index.html", results=scan_result["tracking_pixels"])

    return render_template("index.html", results=None)

@app.route("/download/excel")
def download_excel():
    """Generate and return an Excel file containing the tracking scan results."""
    global last_scan

    if not last_scan or "data" not in last_scan:
        return "No data available", 400

    # Convert results into a DataFrame
    data = []
    for pixel, details in last_scan["data"].items():
        data.append({
            "Tracking Pixel": pixel,
            "Found": "Yes" if details["found"] else "No",
            "Pixel ID": details["pixel_id"] if details["pixel_id"] else "-",
            "Pages Found On": ", ".join(details.get("pages_found", [])) if details.get("pages_found") else "-"
        })

    df = pd.DataFrame(data)

    # Save as Excel file
    file_path = "tracking_results.xlsx"
    df.to_excel(file_path, index=False)

    return send_file(file_path, as_attachment=True)

@app.route("/download/pdf")
def download_pdf():
    """Generate and return a PDF file containing the tracking scan results."""
    global last_scan

    if not last_scan or "data" not in last_scan:
        return "No data available", 400

    # Create HTML content for the PDF
    html_content = """
    <html>
    <head><title>Tracking Pixel Scan Report</title></head>
    <body>
        <h2>Tracking Pixel Scan Report</h2>
        <table border="1" style="width:100%; border-collapse: collapse;">
            <tr>
                <th>Tracking Pixel</th>
                <th>Found?</th>
                <th>Pixel ID</th>
                <th>Pages Found On</th>
            </tr>
    """

    for pixel, details in last_scan["data"].items():
        pages_found = ", ".join(details.get("pages_found", [])) if details.get("pages_found") else "-"
        html_content += f"""
        <tr>
            <td>{pixel}</td>
            <td>{"✅ Yes" if details["found"] else "❌ No"}</td>
            <td>{details["pixel_id"] if details["pixel_id"] else "-"}</td>
            <td>{pages_found}</td>
        </tr>
        """

    html_content += """
        </table>
    </body>
    </html>
    """

    # Convert to PDF
    pdf_file = "tracking_results.pdf"
    HTML(string=html_content).write_pdf(pdf_file)

    return send_file(pdf_file, as_attachment=True)

import os

port = int(os.environ.get("PORT", 10000))  # Render uses PORT variable
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=port)
