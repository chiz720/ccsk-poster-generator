// ═══ QUILL EDITOR SETUP ═══

const TOOLBAR_OPTIONS = [
    ['bold', 'italic', 'underline'],
    [{ 'list': 'ordered'}, { 'list': 'bullet' }],
    ['image'],
    ['clean']
];

// Track all Quill instances
const quillInstances = new Map();
let editorCounter = 0;

function initQuillEditor(container) {
    const id = `editor-${editorCounter++}`;
    container.id = id;

    const quill = new Quill(container, {
        theme: 'snow',
        placeholder: 'Type your content here... Use the toolbar above for bold, lists, and images.',
        modules: {
            toolbar: {
                container: TOOLBAR_OPTIONS,
                handlers: {
                    image: function() {
                        imageHandler(quill);
                    }
                }
            }
        }
    });

    quillInstances.set(id, quill);
    return quill;
}

// Custom image handler — upload then insert
function imageHandler(quill) {
    const input = document.createElement('input');
    input.setAttribute('type', 'file');
    input.setAttribute('accept', 'image/*');
    input.click();

    input.onchange = async () => {
        const file = input.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('image', file);

        try {
            const res = await fetch('/upload-image', { method: 'POST', body: formData });
            const data = await res.json();
            if (data.error) { alert(data.error); return; }

            const range = quill.getSelection(true);
            quill.insertEmbed(range.index, 'image', data.url);
            quill.setSelection(range.index + 1);
        } catch (err) {
            alert('Image upload failed: ' + err.message);
        }
    };
}

// Initialize all editors on page load
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.quill-editor').forEach(el => {
        initQuillEditor(el);
    });
});

// ═══ COLLECT FORM DATA ═══
function gatherData() {
    return {
        title: document.getElementById('title').value,
        authors: document.getElementById('authors').value,
        affiliations: document.getElementById('affiliations').value,
        email: document.getElementById('email').value,
        col1: gatherColumn('col1'),
        col2: gatherColumn('col2'),
        col3: gatherColumn('col3'),
    };
}

function gatherColumn(colId) {
    const sections = [];
    document.querySelectorAll(`#${colId}-sections .section-block`).forEach(block => {
        const editorEl = block.querySelector('.quill-editor');
        const quill = quillInstances.get(editorEl.id);
        const html = quill ? quill.root.innerHTML : '';

        sections.push({
            heading: block.querySelector('.section-heading').value,
            content: html,
            highlighted: block.querySelector('.section-hl').checked,
        });
    });
    return sections;
}

// ═══ ADD / REMOVE SECTIONS ═══
function addSection(colId) {
    const container = document.getElementById(`${colId}-sections`);
    const block = document.createElement('div');
    block.className = 'section-block';
    block.dataset.col = colId;
    block.innerHTML = `
        <input type="text" class="section-heading" placeholder="Section heading">
        <label class="hl-toggle"><input type="checkbox" class="section-hl"> Highlighted section</label>
        <div class="editor-container">
            <div class="quill-editor"></div>
        </div>
        <button class="btn-remove" onclick="removeSection(this)">&times;</button>
    `;
    container.appendChild(block);

    // Initialize the Quill editor for this new section
    const editorEl = block.querySelector('.quill-editor');
    initQuillEditor(editorEl);

    block.querySelector('.section-heading').focus();
}

function removeSection(btn) {
    const block = btn.closest('.section-block');
    const container = block.parentElement;
    if (container.children.length > 1) {
        const editorEl = block.querySelector('.quill-editor');
        if (editorEl && editorEl.id) {
            quillInstances.delete(editorEl.id);
        }
        block.remove();
    }
}

// ═══ PREVIEW ═══
async function previewPoster() {
    const data = gatherData();
    document.body.classList.add('loading');

    try {
        const res = await fetch('/preview', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        const html = await res.text();

        const section = document.getElementById('preview-section');
        section.style.display = 'block';

        const frame = document.getElementById('preview-frame');
        const doc = frame.contentDocument || frame.contentWindow.document;
        doc.open();
        doc.write(html);
        doc.close();

        section.scrollIntoView({ behavior: 'smooth' });
    } catch (err) {
        alert('Preview failed: ' + err.message);
    } finally {
        document.body.classList.remove('loading');
    }
}

// ═══ DOWNLOAD PDF ═══
async function downloadPDF() {
    const data = gatherData();
    document.body.classList.add('loading');

    try {
        const res = await fetch('/download', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });

        if (!res.ok) throw new Error('PDF generation failed');

        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'CCSK_Poster.pdf';
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
    } catch (err) {
        alert('Download failed: ' + err.message);
    } finally {
        document.body.classList.remove('loading');
    }
}
