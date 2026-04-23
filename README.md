# Molloy University Employee Benefits Parser

A two-stage LLM pipeline that ingests, semantically diffs, and visually traces changes between Molloy University's annual employee benefit PDF guides (2024 → 2025).

## Repository Architecture

This codebase is split into three core phases: **PDF Extraction**, **LLM Semantic Diffing**, and a **Visual Verification UI**.

### Core Scripts

| Script | Role |
|---|---|
| `parse_pdfs.py` | Ingests `raw/*.pdf` via IBM Docling; preserves table `bbox` + page numbers into `parsed/*.json` |
| `diff_json.py` | Traverses the Docling JSON tree; maps `TableItem` objects to their nearest section header; exports `diff/changes_geom.json` |
| `llm_diff.py` | Two-stage Gemini pipeline: Stage 1 maps section headers across years; Stage 2 runs parallel async extractions to produce `diff/final_contract_changes.json` |
| `app.py` | Streamlit dashboard — loads both JSON files, renders AI-detected contract changes, and draws PyMuPDF yellow highlight boxes over source PDF pages |

### Legacy / Scaffold Scripts
* **`diff_markdown.py`**: V1 script that diffed using flattened Markdown. Replaced by `diff_json.py` for coordinate support.
* **`main.py`**: Default `uv` scaffold stub, currently unused.

---

## Running the App

> [!NOTE]
> `diff/changes_geom.json` and `diff/final_contract_changes.json` are already committed to the repo.  
> **You only need Steps 1–2** to view the dashboard. Steps 3–5 are only needed if you want to re-run the full pipeline.

### Step 1 — Install Dependencies

```bash
pip install uv
uv sync
```

### Step 2 — Download Source PDFs

The PDF files are too large for git. Fetch them using the provided script:

```bash
bash raw/download.sh
```

This saves `raw/molloy-univ-2024.pdf` and `raw/molloy-univ-2025.pdf`.

### Step 3 — Launch the Dashboard

```bash
uv run streamlit run app.py
```

Open `http://localhost:8501` in your browser.

- Use the **left sidebar** to select a 2024 benefit section (e.g. `Cigna Dental DHMO & DPPO (Page 12)`).
- The **top panel** shows AI-detected contract changes with 🔴 2024 vs 🟢 2025 contrast.
- The **bottom panel** shows side-by-side raw Markdown tables and PDF screenshots with yellow highlights.

---

## Re-running the Full Pipeline (Optional)

Only needed if the source PDFs change or you want fresh LLM analysis.

### Step 4 — Set your Gemini API Key

```bash
cp .env.example .env
# Edit .env and set GEMINI_API_KEY=<your key>
```

### Step 5 — Run the Pipeline

```bash
# 1. Re-parse PDFs → parsed/*.json
uv run python parse_pdfs.py

# 2. Build geometric diff → diff/changes_geom.json
uv run python diff_json.py

# 3. Run LLM semantic diff → diff/final_contract_changes.json  (~4 min)
uv run python llm_diff.py
```
