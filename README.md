# Molloy University Employee Benefits Parser

A structured data pipeline that ingests, diffs, and visually proves changes between annual employee benefit PDF guides.

## Repository Architecture

This codebase is split into three core phases: PDF Extraction, Geometric Diffing, and Visual UI.

### Core Python Scripts
* **`parse_pdfs.py`** 
  The ingestion layer. It uses the `docling` library to parse the bulky `raw/` PDFs (2024 & 2025). It avoids flattened Markdown loss by exporting the rich `DoclingDocument` tree directly into `parsed/*.json`, ensuring all table bounding boxes (`bbox`) and page numbers are preserved.
  
* **`diff_json.py`**
  The semantic diff engine. Instead of using regex on text, it deeply traverses the `DoclingDocument` JSON hierarchy. It maps underlying `TableItem` objects to their nearest `SectionHeaderItem` (e.g. "Dental"), successfully extracting the geometric table coordinates into the final `diff/changes_geom.json` payload.

* **`app.py`**
  The visual verifier. A `streamlit` web application that loads the JSON diff payload. When a user clicks a specific benefit change, it leverages PyMuPDF (`fitz`) in the backend to unearth the raw source PDF, navigate to the exact originating page, and draw a bright yellow highlighter box directly over the coordinates extracted by docling before displaying the resulting picture to the user.

### Legacy / Scaffold Scripts
* **`diff_markdown.py`**: The initial V1 script that attempted to diff tables using purely flattened Markdown heading markers. Replaced by `diff_json.py` to support layout coordinates.
* **`main.py`**: The default `uv inc` scaffold stub, currently unused.

## Getting Started
Ensure all heavy PDFs are enclosed in `raw/` and execute the pipeline sequentially:
```bash
uv run python parse_pdfs.py
uv run python diff_json.py
uv run streamlit run app.py
```
