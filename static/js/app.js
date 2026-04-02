// ═══ COLLECT FORM DATA ═══
function gatherData() {
    const data = {
        title: document.getElementById("title").value,
        authors: document.getElementById("authors").value,
        affiliations: document.getElementById("affiliations").value,
        email: document.getElementById("email").value,
        col1: gatherColumn("col1"),
        col2: gatherColumn("col2"),
        col3: gatherColumn("col3"),
    };
    return data;
}

function gatherColumn(colId) {
    const sections = [];
    document.querySelectorAll(`#${colId}-sections .section-block`).forEach(block => {
        sections.push({
            heading: block.querySelector(".section-heading").value,
            content: block.querySelector(".section-content").value,
            highlighted: block.querySelector(".section-hl").checked,
        });
    });
    return sections;
}

// ═══ ADD / REMOVE SECTIONS ═══
function addSection(colId) {
    const container = document.getElementById(`${colId}-sections`);
    const block = document.createElement("div");
    block.className = "section-block";
    block.dataset.col = colId;
    block.innerHTML = `
        <input type="text" class="section-heading" placeholder="Section heading">
        <label class="hl-toggle"><input type="checkbox" class="section-hl"> Highlighted</label>
        <textarea class="section-content" rows="6" placeholder="Write your content in Markdown..."></textarea>
        <button class="btn-remove" onclick="removeSection(this)">&times;</button>
    `;
    container.appendChild(block);
    block.querySelector(".section-heading").focus();
}

function removeSection(btn) {
    const block = btn.closest(".section-block");
    const container = block.parentElement;
    if (container.children.length > 1) {
        block.remove();
    }
}

// ═══ PREVIEW ═══
async function previewPoster() {
    const data = gatherData();
    document.body.classList.add("loading");

    try {
        const res = await fetch("/preview", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });
        const html = await res.text();

        const section = document.getElementById("preview-section");
        section.style.display = "block";

        const frame = document.getElementById("preview-frame");
        const doc = frame.contentDocument || frame.contentWindow.document;
        doc.open();
        doc.write(html);
        doc.close();

        section.scrollIntoView({ behavior: "smooth" });
    } catch (err) {
        alert("Preview failed: " + err.message);
    } finally {
        document.body.classList.remove("loading");
    }
}

// ═══ DOWNLOAD PDF ═══
async function downloadPDF() {
    const data = gatherData();
    document.body.classList.add("loading");

    try {
        const res = await fetch("/download", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });

        if (!res.ok) throw new Error("PDF generation failed");

        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "CCSK_Poster.pdf";
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
    } catch (err) {
        alert("Download failed: " + err.message);
    } finally {
        document.body.classList.remove("loading");
    }
}

// ═══ IMAGE UPLOAD ═══
async function uploadImage() {
    const input = document.getElementById("image-upload");
    if (!input.files.length) return;

    const formData = new FormData();
    formData.append("image", input.files[0]);

    try {
        const res = await fetch("/upload-image", {
            method: "POST",
            body: formData,
        });
        const data = await res.json();
        if (data.error) {
            alert(data.error);
            return;
        }

        const container = document.getElementById("uploaded-images");
        const item = document.createElement("div");
        item.className = "uploaded-item";
        const mdTag = `![Figure](${data.url})`;
        item.innerHTML = `
            <img src="${data.url}" alt="${data.filename}">
            <code onclick="copyToClipboard(this)" title="Click to copy">![Figure](uploaded)</code>
        `;
        // Store the actual data URL on the code element
        item.querySelector("code").dataset.md = mdTag;
        container.appendChild(item);
        input.value = "";
    } catch (err) {
        alert("Upload failed: " + err.message);
    }
}

function copyToClipboard(el) {
    const text = el.dataset.md || el.textContent;
    navigator.clipboard.writeText(text).then(() => {
        const orig = el.textContent;
        el.textContent = "Copied!";
        setTimeout(() => { el.textContent = orig; }, 1500);
    });
}

// ═══ COLLAPSIBLE ═══
function toggleCollapse(header) {
    header.closest(".collapsible").classList.toggle("collapsed");
}

// Start collapsed
document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".collapsible").forEach(el => el.classList.add("collapsed"));
});
