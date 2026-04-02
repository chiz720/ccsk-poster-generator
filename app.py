import os
import uuid
import base64
from flask import Flask, render_template, request, send_file, jsonify
from weasyprint import HTML

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
    pdf_path = os.path.join(app.config["UPLOAD_FOLDER"], f"poster_{uuid.uuid4().hex[:8]}.pdf")
    HTML(string=html).write_pdf(pdf_path)
    return send_file(pdf_path, as_attachment=True, download_name="CCSK_Poster.pdf")


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
@page {{
    size: 841mm 594mm;
    margin: 0;
}}

* {{
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}}

body {{
    font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    font-size: 11pt;
    color: #2a2a2a;
    background: white;
    width: 841mm;
    height: 594mm;
}}

/* ═══ BANNER ═══ */
.banner {{
    background: linear-gradient(135deg, #1B2A4A 0%, #304E78 40%, #3C608C 60%, #1B2A4A 100%);
    color: white;
    padding: 18mm 25mm;
    position: relative;
    height: 52mm;
    display: flex;
    align-items: center;
}}

.banner-text {{
    flex: 1;
}}

.banner h1 {{
    font-size: 32pt;
    font-weight: 800;
    margin-bottom: 4mm;
    line-height: 1.2;
}}

.banner .authors {{
    font-size: 15pt;
    margin-bottom: 2mm;
}}

.banner .affiliations {{
    font-size: 11pt;
    opacity: 0.8;
}}

.banner .logo {{
    width: 38mm;
    height: 38mm;
    border-radius: 50%;
    background: white;
    padding: 2mm;
    margin-left: 15mm;
    flex-shrink: 0;
}}

.banner .logo img {{
    width: 100%;
    height: 100%;
    border-radius: 50%;
    object-fit: contain;
}}

/* ═══ CONTENT ═══ */
.content {{
    display: flex;
    padding: 6mm 8mm;
    gap: 6mm;
    height: 524mm;
}}

.column {{
    flex: 1;
    overflow: hidden;
}}

/* ═══ BLOCKS ═══ */
.block {{
    margin-bottom: 5mm;
}}

.block h3 {{
    font-size: 15pt;
    font-weight: 700;
    text-align: center;
    padding-bottom: 2mm;
    border-bottom: 0.6pt solid #1B2A4A;
    margin-bottom: 3mm;
    color: #1B2A4A;
}}

.block-body {{
    font-size: 10.5pt;
    line-height: 1.45;
    text-align: justify;
    hyphens: auto;
}}

.block-body p {{
    margin-bottom: 2mm;
}}

.block-body ul, .block-body ol {{
    margin: 2mm 0 2mm 5mm;
    padding-left: 3mm;
}}

.block-body li {{
    margin-bottom: 1mm;
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
    margin: 3mm 0;
    font-size: 10pt;
}}

.block-body th {{
    border-top: 1.5pt solid black;
    border-bottom: 0.8pt solid black;
    padding: 1.5mm 2mm;
    font-weight: 700;
    text-align: center;
}}

.block-body td {{
    padding: 1.2mm 2mm;
    text-align: center;
    border-bottom: 0.3pt solid #ddd;
}}

.block-body tr:last-child td {{
    border-bottom: 1pt solid black;
}}

.block-body img {{
    max-width: 100%;
    height: auto;
    display: block;
    margin: 3mm auto;
}}

.block-body code {{
    background: #f0f0f0;
    padding: 0.5mm 1.5mm;
    border-radius: 1mm;
    font-size: 9.5pt;
}}

/* ═══ HIGHLIGHTED BLOCK ═══ */
.highlighted {{
    background: #E8EDF4;
    border: 0.5pt solid #B0BBD0;
    padding: 4mm;
    border-radius: 1mm;
    margin-bottom: 5mm;
}}

.highlighted h3 {{
    border-bottom-color: #1B2A4A;
}}

/* ═══ FOOTER ═══ */
.footer {{
    background: #1B2A4A;
    color: white;
    height: 12mm;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 25mm;
    font-size: 10pt;
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
}}

.footer a {{
    color: white;
    text-decoration: none;
}}
</style>
</head>
<body>

<div class="banner">
    <div class="banner-text">
        <h1>{title}</h1>
        <div class="authors">{authors}</div>
        <div class="affiliations">{affiliations}</div>
    </div>
    <div class="logo">
        <img src="data:image/png;base64,{LOGO_B64}" alt="CCSK Logo">
    </div>
</div>

<div class="content">
    <div class="column">{col1_html}</div>
    <div class="column">{col2_html}</div>
    <div class="column">{col3_html}</div>
</div>

<div class="footer">
    <span>13th CCSK Annual Scientific Critical Care Congress</span>
    <span>13&ndash;15 May 2026 &bull; Argyle Grand Hotel, Nairobi</span>
    <span>{email}</span>
</div>

</body>
</html>"""


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5555))
    debug = os.environ.get("FLASK_ENV") != "production"
    app.run(debug=debug, host="0.0.0.0", port=port)
