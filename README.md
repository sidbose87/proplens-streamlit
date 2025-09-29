# PropLens MVP


A Streamlit MVP that:
- Autocompletes and geocodes Australian addresses using OpenStreetMap Nominatim.
- Finds candidate listing URLs and, if allowed by robots.txt, fetches pages and extracts Schema.org JSON-LD.
- Optionally augments with NSW open datasets (stubs provided, safe fallbacks only).
- Normalises to PropertyFacts with per-field source and confidence.
- Computes Expenses and Bank + Cashflow outputs with sliders.
- Shows source URLs and timestamps.


No paid APIs. No headless browsing. Respects robots.txt and ToS. A global toggle `ALLOW_WEB_FETCH` lets you disable third-party fetches quickly.


## Quick start


```bash
python -m venv .venv
source .venv/bin/activate # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
streamlit run app.py