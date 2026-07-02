from pathlib import Path
import re
import io
import zipfile
import tempfile
import shutil

import fitz  # PyMuPDF
import streamlit as st

st.set_page_config(page_title="PDF Pages to Images", page_icon="🧾", layout="wide")


def safe_name(name: str) -> str:
    name = re.sub(r'[\\/:*?"<>|]+', '_', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name[:120] if name else 'page'


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    counter = 2
    while True:
        candidate = parent / f"{stem} ({counter}){suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def get_page_title(page: fitz.Page) -> str:
    data = page.get_text("dict")
    best_span = None

    for block in data.get("blocks", []):
        if "lines" not in block:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                text = span["text"].strip()
                if not text:
                    continue
                y0 = span["bbox"][1]
                size = span["size"]
                if best_span is None:
                    best_span = (text, size, y0)
                else:
                    _, best_size, best_y = best_span
                    if size > best_size + 0.5 or (abs(size - best_size) < 0.5 and y0 < best_y):
                        best_span = (text, size, y0)
    return best_span[0] if best_span else ""


def convert_pdf_bytes(pdf_bytes: bytes, original_name: str, zoom: float = 2.0):
    results = []
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        pdf_stem = safe_name(Path(original_name).stem)
        out_dir = tmp_path / pdf_stem
        out_dir.mkdir(parents=True, exist_ok=True)

        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        for i, page in enumerate(doc, start=1):
            title_raw = get_page_title(page) or f"page_{i}"
            title = safe_name(title_raw)
            image_path = unique_path(out_dir / f"{title}.png")
            pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
            pix.save(str(image_path))
            results.append({
                "page": i,
                "title": title,
                "path": image_path,
                "folder": pdf_stem,
                "filename": image_path.name,
            })
        doc.close()

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for item in results:
                arcname = f"{item['folder']}/{item['filename']}"
                zf.write(item["path"], arcname)
        zip_buffer.seek(0)

        preview_images = []
        for item in results[:5]:
            preview_images.append((item["filename"], item["path"].read_bytes()))

        return results, zip_buffer.getvalue(), preview_images


st.title("PDF Pages to Images")
st.write("Upload one or more PDF files. Each page is converted to a PNG and named from the large title at the top of the page.")

col1, col2 = st.columns([2, 1])
with col1:
    uploaded_files = st.file_uploader(
        "Upload PDFs",
        type=["pdf"],
        accept_multiple_files=True,
        help="You can select multiple PDF files in one go."
    )
with col2:
    zoom = st.slider("Image quality", min_value=1.0, max_value=3.0, value=2.0, step=0.5)

process = st.button("Convert PDFs", type="primary", disabled=not uploaded_files)

if process and uploaded_files:
    for uploaded in uploaded_files:
        with st.container(border=True):
            st.subheader(uploaded.name)
            with st.spinner(f"Processing {uploaded.name}..."):
                results, zip_bytes, previews = convert_pdf_bytes(uploaded.getvalue(), uploaded.name, zoom=zoom)

            st.success(f"Created {len(results)} page images.")
            st.download_button(
                label=f"Download {Path(uploaded.name).stem} images (.zip)",
                data=zip_bytes,
                file_name=f"{safe_name(Path(uploaded.name).stem)}_images.zip",
                mime="application/zip",
                use_container_width=True,
            )

            with st.expander("See extracted filenames", expanded=True):
                for item in results:
                    st.write(f"Page {item['page']}: {item['filename']}")

            if previews:
                st.caption("Preview of first few generated images")
                preview_cols = st.columns(min(3, len(previews)))
                for idx, (name, img_bytes) in enumerate(previews):
                    with preview_cols[idx % len(preview_cols)]:
                        st.image(img_bytes, caption=name, use_container_width=True)
