from pathlib import Path
import re
import io
import zipfile
import tempfile

import fitz  # PyMuPDF
import streamlit as st

st.set_page_config(
    page_title="PDF Page Exporter",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
        :root {
            --app-bg: oklch(0.975 0 0);
            --surface: oklch(1 0 0);
            --surface-subtle: oklch(0.955 0.008 140);
            --ink: oklch(0.19 0.025 140);
            --muted: oklch(0.46 0.02 140);
            --line: oklch(0.88 0.012 140);
            --primary: oklch(0.35 0.11 140);
            --primary-hover: oklch(0.30 0.105 140);
            --accent: oklch(0.58 0.13 235);
            --focus: var(--accent);
        }

        html { color-scheme: light; }
        .stApp { background: var(--app-bg); color: var(--ink); }
        .block-container {
            max-width: 1080px;
            padding-top: 3.5rem;
            padding-bottom: 5rem;
        }
        header[data-testid="stHeader"] { background: transparent; }

        .app-hero {
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 2.5rem;
        }
        .app-mark {
            display: grid;
            place-items: center;
            width: 3.25rem;
            height: 3.25rem;
            flex: 0 0 auto;
            border-radius: 0.8rem;
            background: var(--primary);
            color: oklch(1 0 0);
            font-size: 0.72rem;
            font-weight: 750;
            letter-spacing: 0.04em;
            box-shadow: 0 0.5rem 1.5rem oklch(0.35 0.11 140 / 0.18);
        }
        .app-hero h1 {
            margin: 0 0 0.25rem;
            color: var(--ink);
            font-size: 2rem;
            line-height: 1.15;
            letter-spacing: -0.025em;
            text-wrap: balance;
        }
        .app-hero p {
            max-width: 68ch;
            margin: 0;
            color: var(--muted);
            font-size: 1rem;
            line-height: 1.55;
            text-wrap: pretty;
        }
        .workflow-note {
            display: flex;
            flex-wrap: wrap;
            gap: 0.65rem 1.25rem;
            margin: -1rem 0 2.25rem;
            color: var(--muted);
            font-size: 0.875rem;
        }
        .workflow-note span { white-space: nowrap; }
        .workflow-note strong { color: var(--ink); }

        h2, h3 { color: var(--ink); letter-spacing: -0.015em; }
        div[data-testid="stFileUploaderDropzone"] {
            min-height: 12rem;
            border: 1.5px dashed var(--line) !important;
            border-radius: 0.9rem;
            background: var(--surface) !important;
            color: var(--ink) !important;
            transition: border-color 180ms ease-out, background 180ms ease-out;
        }
        div[data-testid="stFileUploaderDropzone"]:hover {
            border-color: var(--focus) !important;
            background: var(--surface-subtle) !important;
        }
        div[data-testid="stFileUploaderDropzone"] button {
            border-color: var(--primary) !important;
            background: var(--primary) !important;
            color: oklch(1 0 0) !important;
            font-weight: 650;
        }
        div[data-testid="stFileUploaderDropzone"] button:hover {
            border-color: var(--primary-hover) !important;
            background: var(--primary-hover) !important;
        }
        div[data-testid="stFileUploaderDropzone"] button p,
        div[data-testid="stFileUploaderDropzone"] button span {
            color: oklch(1 0 0) !important;
        }
        div[data-testid="stFileUploaderDropzone"] button svg {
            fill: oklch(1 0 0) !important;
            color: oklch(1 0 0) !important;
        }
        div[data-testid="stFileUploaderDropzone"] small,
        div[data-testid="stFileUploaderDropzone"] > div > span {
            color: var(--muted) !important;
        }
        div[data-testid="stFileUploaderFile"] {
            border-radius: 0.65rem;
            background: var(--surface) !important;
            color: var(--ink) !important;
        }
        div[data-testid="stSlider"] label,
        div[data-testid="stSlider"] p {
            color: var(--ink) !important;
        }

        div[data-testid="stButton"] > button[kind="primary"],
        div[data-testid="stDownloadButton"] > button {
            min-height: 2.8rem;
            border: 1px solid var(--primary);
            border-radius: 0.65rem;
            background: var(--primary);
            color: oklch(1 0 0);
            font-weight: 650;
            transition: background 180ms ease-out, border-color 180ms ease-out,
                        transform 180ms ease-out;
        }
        div[data-testid="stButton"] > button[kind="primary"]:hover,
        div[data-testid="stDownloadButton"] > button:hover {
            border-color: var(--primary-hover);
            background: var(--primary-hover);
            color: oklch(1 0 0);
            transform: translateY(-1px);
        }
        div[data-testid="stButton"] > button:focus-visible,
        div[data-testid="stDownloadButton"] > button:focus-visible {
            outline: 3px solid oklch(0.68 0.13 140 / 0.35);
            outline-offset: 2px;
        }
        div[data-testid="stButton"] > button:disabled {
            border-color: var(--line);
            background: oklch(0.89 0.008 140);
            color: oklch(0.47 0.015 140);
        }

        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-color: var(--line) !important;
            border-radius: 0.9rem !important;
            background: var(--surface);
            box-shadow: 0 0.35rem 1.5rem oklch(0.19 0.025 140 / 0.045);
        }
        div[data-testid="stAlert"] { border-radius: 0.65rem; }
        div[data-testid="stExpander"] {
            border-color: var(--line);
            border-radius: 0.65rem;
        }
        div[data-testid="stImage"] img { border-radius: 0.55rem; }
        .result-meta { color: var(--muted); font-size: 0.9rem; }
        .result-counts {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem 1.15rem;
            margin-top: 0.65rem;
            color: var(--muted);
            font-size: 0.9rem;
        }
        .result-counts strong { color: var(--ink); font-weight: 700; }

        @media (max-width: 640px) {
            .block-container { padding-top: 2rem; }
            .app-hero { align-items: flex-start; }
            .app-hero h1 { font-size: 1.65rem; }
            .app-mark { width: 2.8rem; height: 2.8rem; }
        }
        @media (prefers-reduced-motion: reduce) {
            *, *::before, *::after {
                scroll-behavior: auto !important;
                transition-duration: 0.01ms !important;
            }
        }
    </style>
    """,
    unsafe_allow_html=True,
)


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


def get_manager_name(page: fitz.Page) -> str:
    """Return the value next to or below a supported manager label."""
    lines = [
        re.sub(r'\s+', ' ', line).strip()
        for line in page.get_text("text", sort=True).splitlines()
        if line.strip()
    ]

    for index, line in enumerate(lines):
        match = re.match(
            r'^(?:research\s+analyst|investment\s+advisor)\b\s*[:\-]?\s*(.*)$',
            line,
            re.IGNORECASE,
        )
        if not match:
            continue

        # Some PDFs place the value on the same line as the label.
        inline_value = match.group(1).strip()
        if inline_value:
            return inline_value

        # In the usual report layout, the value is the next extracted line.
        if index + 1 < len(lines):
            return lines[index + 1]

    return ""


def convert_pdf_bytes(pdf_bytes: bytes, original_name: str, zoom: float = 2.0):
    results = []
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        pdf_stem = safe_name(Path(original_name).stem)
        out_dir = tmp_path / pdf_stem
        out_dir.mkdir(parents=True, exist_ok=True)

        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        total_pages = len(doc)
        for i, page in enumerate(doc, start=1):
            manager_raw = get_manager_name(page)

            # Portfolio detail pages contain one of the supported manager
            # labels. Generic cover, how-to, performance, and ending pages do
            # not, so they are excluded from the output.
            if not manager_raw:
                continue

            title_raw = get_page_title(page) or f"page_{i}"
            display_name = f"{title_raw} by {manager_raw}"
            title = safe_name(display_name)
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

        return total_pages, results, zip_buffer.getvalue(), preview_images


def format_file_size(size_bytes: int) -> str:
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.1f} MB"


def output_zip_name(original_name: str) -> str:
    return f"{safe_name(Path(original_name).stem)}_images.zip"


def create_batch_zip(outputs: list[dict]) -> bytes:
    """Bundle each successful per-PDF ZIP into one download archive."""
    batch_buffer = io.BytesIO()
    used_names = {}

    # The inner files are already compressed ZIPs, so storing them directly
    # avoids wasting time trying to compress the same bytes again.
    with zipfile.ZipFile(batch_buffer, "w", zipfile.ZIP_STORED) as archive:
        for output in outputs:
            if output["error"] is not None or not output["results"]:
                continue

            base_name = output_zip_name(output["original_name"])
            used_names[base_name] = used_names.get(base_name, 0) + 1
            occurrence = used_names[base_name]
            if occurrence == 1:
                archive_name = base_name
            else:
                zip_path = Path(base_name)
                archive_name = f"{zip_path.stem} ({occurrence}){zip_path.suffix}"

            archive.writestr(archive_name, output["zip_bytes"])

    batch_buffer.seek(0)
    return batch_buffer.getvalue()


st.markdown(
    """
    <div class="app-hero">
        <div class="app-mark">PNG</div>
        <div>
            <h1>PDF page exporter</h1>
            <p>Extract portfolio detail pages as crisp PNGs, automatically named using the title and its Research Analyst or Investment Advisor.</p>
        </div>
    </div>
    <div class="workflow-note" aria-label="Conversion steps">
        <span><strong>1.</strong> Select one or more PDFs</span>
        <span><strong>2.</strong> Keep manager-labelled pages</span>
        <span><strong>3.</strong> Download a separate ZIP for each PDF</span>
    </div>
    """,
    unsafe_allow_html=True,
)

st.subheader("Upload PDFs")
st.caption("Select multiple files in one go. Each PDF is processed independently.")
st.info(
    "**Pages skipped:** cover or welcome pages, how-to or instruction pages, "
    "performance pages, disclaimers, and ending or thank-you pages. The app "
    "exports only pages that contain a **Research Analyst** or "
    "**Investment Advisor** label."
)
uploaded_files = st.file_uploader(
    "Choose PDF files",
    type=["pdf"],
    accept_multiple_files=True,
    help="Drag and drop several PDF files here, or browse to select them.",
    label_visibility="collapsed",
)

control_col, action_col = st.columns([1.15, 1], vertical_alignment="bottom")
with control_col:
    zoom = st.select_slider(
        "Image resolution",
        options=[1.0, 1.5, 2.0, 2.5, 3.0],
        value=2.0,
        format_func=lambda value: {
            1.0: "Standard",
            1.5: "Balanced",
            2.0: "High",
            2.5: "Very high",
            3.0: "Maximum",
        }[value],
        help="Higher resolution creates sharper PNGs and larger ZIP files.",
    )

file_count = len(uploaded_files) if uploaded_files else 0
with action_col:
    process = st.button(
        f"Convert {file_count} PDF{'s' if file_count != 1 else ''}",
        type="primary",
        disabled=not uploaded_files,
        use_container_width=True,
    )

if uploaded_files:
    total_upload_size = sum(uploaded.size for uploaded in uploaded_files)
    st.info(
        f"Ready to process {file_count} PDF{'s' if file_count != 1 else ''} "
        f"({format_file_size(total_upload_size)} total)."
    )

if "conversion_outputs" not in st.session_state:
    st.session_state.conversion_outputs = []

if process and uploaded_files:
    batch_outputs = []
    progress_bar = st.progress(0)
    progress_text = st.empty()

    for index, uploaded in enumerate(uploaded_files, start=1):
        progress_text.caption(f"Processing {index} of {file_count}: {uploaded.name}")
        try:
            total_pages, results, zip_bytes, previews = convert_pdf_bytes(
                uploaded.getvalue(),
                uploaded.name,
                zoom=zoom,
            )
            batch_outputs.append({
                "original_name": uploaded.name,
                "total_pages": total_pages,
                "results": results,
                "zip_bytes": zip_bytes,
                "previews": previews,
                "error": None,
            })
        except Exception as exc:
            batch_outputs.append({
                "original_name": uploaded.name,
                "total_pages": 0,
                "results": [],
                "zip_bytes": b"",
                "previews": [],
                "error": str(exc),
            })
        progress_bar.progress(index / file_count)

    st.session_state.conversion_outputs = batch_outputs
    progress_bar.empty()
    progress_text.empty()

if st.session_state.conversion_outputs:
    st.divider()
    st.subheader("Your downloads")
    st.caption(
        "Download every PDF separately, or download one master ZIP containing "
        "all the individual ZIP files."
    )

    successful_outputs = sum(
        output["error"] is None for output in st.session_state.conversion_outputs
    )
    downloadable_outputs = [
        output
        for output in st.session_state.conversion_outputs
        if output["error"] is None and output["results"]
    ]

    summary_col, batch_download_col = st.columns(
        [1.7, 1],
        vertical_alignment="center",
    )
    with summary_col:
        if successful_outputs:
            st.success(
                f"Finished {successful_outputs} of "
                f"{len(st.session_state.conversion_outputs)} PDF files."
            )
    with batch_download_col:
        if downloadable_outputs:
            batch_zip_bytes = create_batch_zip(downloadable_outputs)
            st.download_button(
                label=f"Download all {len(downloadable_outputs)} ZIPs",
                data=batch_zip_bytes,
                file_name="all_pdf_image_zips.zip",
                mime="application/zip",
                key="download_all_zips",
                use_container_width=True,
            )

    for output_index, output in enumerate(st.session_state.conversion_outputs):
        with st.container(border=True):
            if output["error"]:
                st.subheader(output["original_name"])
                st.error(f"This PDF could not be processed: {output['error']}")
                continue

            result_col, download_col = st.columns([1.7, 1], vertical_alignment="center")
            with result_col:
                st.subheader(output["original_name"])
                converted_count = len(output["results"])
                total_pages = output["total_pages"]
                skipped_count = total_pages - converted_count
                st.markdown(
                    '<div class="result-counts">'
                    f'<span><strong>{total_pages}</strong> total pages</span>'
                    f'<span><strong>{converted_count}</strong> converted</span>'
                    f'<span><strong>{skipped_count}</strong> skipped</span>'
                    '</div>',
                    unsafe_allow_html=True,
                )
            with download_col:
                zip_name = output_zip_name(output["original_name"])
                if converted_count:
                    st.download_button(
                        label="Download ZIP",
                        data=output["zip_bytes"],
                        file_name=zip_name,
                        mime="application/zip",
                        key=f"download_{output_index}_{zip_name}",
                        use_container_width=True,
                    )

            if not converted_count:
                st.warning(
                    "No portfolio pages with a Research Analyst or Investment Advisor "
                    "were found in this PDF."
                )
                continue

            with st.expander(f"View all {converted_count} filenames"):
                for item in output["results"]:
                    st.write(f"Page {item['page']}: `{item['filename']}`")

            if output["previews"]:
                st.caption("Preview of the first five pages")
                preview_cols = st.columns(min(3, len(output["previews"])))
                for preview_index, (name, img_bytes) in enumerate(output["previews"]):
                    with preview_cols[preview_index % len(preview_cols)]:
                        st.image(img_bytes, caption=name, use_container_width=True)
