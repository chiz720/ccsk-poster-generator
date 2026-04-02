import os
import uuid
import base64
from flask import Flask, render_template, request, send_file, jsonify
from playwright.sync_api import sync_playwright

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(__file__), "static", "uploads")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Logo as base64 for embedding in PDF
LOGO_PATH = os.path.join(os.path.dirname(__file__), "static", "ccsk_logo.png")
with open(LOGO_PATH, "rb") as f:
    LOGO_B64 = base64.b64encode(f.read()).decode()


def clean_html(text):
    """Sanitize HTML content from the rich text editor."""
    if not text:
        return ""
    # Strip any script tags for safety
    import re
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
    return text


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/preview", methods=["POST"])
def preview():
    data = request.get_json()
    html = build_poster_html(data)
    return html


@app.route("/download", methods=["POST"])
def download():
    data = request.get_json()
    html = build_poster_html(data)
    # Save HTML to a temp file for Playwright to load
    html_fname = f"poster_{uuid.uuid4().hex[:8]}.html"
    html_path = os.path.join(app.config["UPLOAD_FOLDER"], html_fname)
    with open(html_path, "w") as f:
        f.write(html)

    png_path = os.path.join(app.config["UPLOAD_FOLDER"], f"poster_{uuid.uuid4().hex[:8]}.png")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 3840, "height": 2160})
        page.goto(f"file://{html_path}")
        page.wait_for_load_state("networkidle")
        page.screenshot(path=png_path, full_page=False)
        browser.close()

    # Clean up temp HTML
    os.remove(html_path)

    return send_file(png_path, as_attachment=True, download_name="CCSK_Poster.png")


@app.route("/fullscreen", methods=["POST"])
def fullscreen():
    """Save poster HTML and redirect to a fullscreen view."""
    data = request.get_json()
    html = build_poster_html(data)
    fname = f"poster_{uuid.uuid4().hex[:8]}.html"
    fpath = os.path.join(app.config["UPLOAD_FOLDER"], fname)
    with open(fpath, "w") as f:
        f.write(html)
    return jsonify({"url": f"/static/uploads/{fname}"})


@app.route("/upload-image", methods=["POST"])
def upload_image():
    if "image" not in request.files:
        return jsonify({"error": "No image"}), 400
    f = request.files["image"]
    ext = f.filename.rsplit(".", 1)[-1].lower()
    if ext not in ("png", "jpg", "jpeg", "gif", "svg"):
        return jsonify({"error": "Invalid format"}), 400
    fname = f"{uuid.uuid4().hex[:8]}.{ext}"
    fpath = os.path.join(app.config["UPLOAD_FOLDER"], fname)
    f.save(fpath)
    with open(fpath, "rb") as img:
        b64 = base64.b64encode(img.read()).decode()
    mime = "image/png" if ext == "png" else "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
    return jsonify({"url": f"data:{mime};base64,{b64}", "filename": fname})


def build_poster_html(data):
    title = data.get("title", "Untitled")
    authors = data.get("authors", "")
    affiliations = data.get("affiliations", "")
    email = data.get("email", "")

    col1_sections = data.get("col1", [])
    col2_sections = data.get("col2", [])
    col3_sections = data.get("col3", [])

    def render_sections(sections):
        html = ""
        for sec in sections:
            heading = sec.get("heading", "")
            content = clean_html(sec.get("content", ""))
            highlighted = sec.get("highlighted", False)
            hl_class = ' class="highlighted"' if highlighted else ""
            html += f"""
            <div class="block"{hl_class if not highlighted else ""}>
                {"<div class='highlighted'>" if highlighted else ""}
                <h3>{heading}</h3>
                <div class="block-body">{content}</div>
                {"</div>" if highlighted else ""}
            </div>
            """
        return html

    col1_html = render_sections(col1_sections)
    col2_html = render_sections(col2_sections)
    col3_html = render_sections(col3_sections)

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

@page {{
    size: 3840px 2160px;
    margin: 0;
}}

* {{
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}}

body {{
    font-family: 'Inter', 'DejaVu Sans', 'Liberation Sans', sans-serif;
    font-size: 38px;
    color: #1a1a1a;
    -webkit-font-smoothing: antialiased;
    text-rendering: optimizeLegibility;
    background: white;
    width: 3840px;
    height: 2160px;
}}

/* ═══ BANNER ═══ */
.banner {{
    background: linear-gradient(135deg, #1B2A4A 0%, #304E78 40%, #3C608C 60%, #1B2A4A 100%);
    color: white;
    height: 340px;
    width: 100%;
    border-collapse: collapse;
}}

.banner td {{
    vertical-align: middle;
    padding: 40px 60px;
}}

.banner .banner-text-cell {{
    text-align: center;
}}

.banner h1 {{
    font-size: 96px;
    font-weight: 800;
    margin-bottom: 12px;
    line-height: 1.2;
}}

.banner .authors {{
    font-size: 48px;
    margin-bottom: 6px;
}}

.banner .affiliations {{
    font-size: 38px;
    opacity: 0.85;
}}

.banner .logo-cell {{
    width: 240px;
    text-align: center;
}}

.banner .logo-cell img {{
    width: 180px;
    height: 180px;
    border-radius: 50%;
    background: white;
    padding: 8px;
}}

/* ═══ CONTENT ═══ */
.content {{
    width: 100%;
    height: 1700px;
    border-collapse: separate;
    border-spacing: 6px 0;
    table-layout: fixed;
    background: #B0BBD0;
}}

.content td {{
    width: 33.333%;
    vertical-align: top;
    padding: 36px 40px;
    background: #FFFFFF;
}}

.content td:first-child {{
    background: #F4F6FA;
}}

.content td:last-child {{
    background: #F4F6FA;
}}

/* ═══ BLOCKS ═══ */
.block {{
    margin-bottom: 28px;
}}

.block h3 {{
    font-size: 56px;
    font-weight: 700;
    text-align: center;
    padding-bottom: 10px;
    border-bottom: none;
    margin-bottom: 16px;
    color: #1B2A4A;
}}

.block-body {{
    font-size: 38px;
    font-weight: 400;
    line-height: 1.6;
    text-align: justify;
    hyphens: auto;
    color: #1a1a1a;
}}

.block-body p {{
    margin-bottom: 12px;
}}

.block-body ul, .block-body ol {{
    margin: 10px 0 10px 24px;
    padding-left: 16px;
}}

.block-body li {{
    margin-bottom: 6px;
}}

.block-body strong {{
    font-weight: 700;
}}

.block-body em {{
    font-style: italic;
}}

.block-body table {{
    width: 100%;
    border-collapse: collapse;
    margin: 14px 0;
    font-size: 34px;
}}

.block-body th {{
    border-top: 3px solid black;
    border-bottom: 2px solid black;
    padding: 8px 12px;
    font-weight: 700;
    text-align: center;
}}

.block-body td {{
    padding: 6px 12px;
    text-align: center;
    border-bottom: 1px solid #ddd;
}}

.block-body tr:last-child td {{
    border-bottom: 2px solid black;
}}

.block-body img {{
    max-width: 100%;
    height: auto;
    display: block;
    margin: 14px auto;
}}

.block-body code {{
    background: #f0f0f0;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 34px;
}}

/* ═══ HIGHLIGHTED BLOCK ═══ */
.highlighted {{
    background: #E8EDF4;
    border: 2px solid #B0BBD0;
    padding: 20px;
    border-radius: 6px;
    margin-bottom: 28px;
}}

.highlighted h3 {{
    border-bottom-color: #1B2A4A;
}}

/* ═══ FOOTER ═══ */
.footer {{
    background: #1B2A4A;
    color: white;
    height: 120px;
    width: 100%;
    border-collapse: collapse;
    font-size: 34px;
}}

.footer td {{
    vertical-align: middle;
    padding: 0 60px;
}}

.footer td:nth-child(2) {{
    text-align: center;
}}

.footer td:nth-child(3) {{
    text-align: right;
}}

.footer a {{
    color: white;
    text-decoration: none;
}}
</style>
</head>
<body>

<table class="banner"><tr>
    <td class="logo-cell">
        <img src="data:image/png;base64,{LOGO_B64}" alt="CCSK Logo">
    </td>
    <td class="banner-text-cell">
        <h1>{title}</h1>
        <div class="authors">{authors}</div>
        <div class="affiliations">{affiliations}</div>
    </td>
    <td class="logo-cell">
        <img src="data:image/png;base64,{LOGO_B64}" alt="CCSK Logo">
    </td>
</tr></table>

<table class="content"><tr>
    <td>{col1_html}</td>
    <td class="col-even">{col2_html}</td>
    <td>{col3_html}</td>
</tr></table>

<table class="footer"><tr>
    <td>13th CCSK Annual Scientific Critical Care Congress</td>
    <td>13&ndash;15 May 2026 &bull; Argyle Grand Hotel, Nairobi</td>
    <td>{email}</td>
</tr></table>

</body>
</html>"""


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5555))
    debug = os.environ.get("FLASK_ENV") != "production"
    app.run(debug=debug, host="0.0.0.0", port=port)
