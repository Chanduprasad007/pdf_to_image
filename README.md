# PDF Pages to Images Web App

A simple Streamlit web app that:
- uploads one or more PDF files
- converts each page into a PNG image
- names each image using the detected large title and Research Analyst in the
  format `<title> by <research analyst>`
- creates a ZIP download per PDF

## Setup

```bash
cd ~/output/pdf_webapp
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

## Run

```bash
cd ~/output/pdf_webapp
source .venv/bin/activate
streamlit run app.py
```

Then open the local URL shown by Streamlit in your browser.
