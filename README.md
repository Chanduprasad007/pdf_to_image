# PDF Pages to Images Web App

A simple Streamlit web app that:
- uploads and processes multiple PDF files in one batch
- converts portfolio detail pages into PNG images
- skips generic introduction, how-to, performance, and ending pages by only
  including pages with a Research Analyst or Investment Advisor label
- names pages with a Research Analyst or Investment Advisor in the format
  `<title> by <manager name>`
- uses the detected page title (or `page_<number>`) when neither manager label
  is present
- creates a separate ZIP download for every uploaded PDF
- reports total, converted, and skipped page counts for each PDF

## Setup

```bash
cd /path/to/pdf_to_image-main
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

## Run

```bash
cd /path/to/pdf_to_image-main
source .venv/bin/activate
streamlit run app.py
```

Then open the local URL shown by Streamlit in your browser.
