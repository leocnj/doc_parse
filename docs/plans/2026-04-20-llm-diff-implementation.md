# LLM Semantic Diff Implementation Plan

> **For Antigravity:** REQUIRED WORKFLOW: Use `.agent/workflows/execute-plan.md` to execute this plan in single-flow mode.

**Goal:** Implement a fast, robust two-stage Gemini pipeline to semantically diff 2024 and 2025 document extractions and map those string descriptions back to local geometric coordinate bounds.

**Architecture:** A standalone Python script `llm_diff.py` handles reading the grouped Docling JSONs, calling `gemini-2.5-flash-lite` to resolve section mapping disparities structurally, and firing parallel `asyncio.gather` calls mapped by Pydantic against `gemini-2.5-flash` to extract explicit numerical and benefit contract changes out of the Markdown.

**Tech Stack:** python 3.12, google-genai, pydantic, asyncio, pytest

---

### Task 1: Environment and Schema Definition

**Files:**
- Modify: `pyproject.toml`
- Create: `llm_diff.py`
- Create: `tests/test_llm_diff.py`

**Step 1: Write the schema tests**
```python
# Create tests/test_llm_diff.py
from llm_diff import ChangeReport, MappingReport

def test_change_report_schema():
    data = {
        "summary": "Increased copay",
        "original_texts": "$10 -> $15",
        "meta_data": {"page_no": 1, "bbox": {"l": 0, "t": 0, "r": 10, "b": 10}}
    }
    report = ChangeReport(**data)
    assert report.summary == "Increased copay"

def test_mapping_report_schema():
    mapping = MappingReport(pairings={"Dental 2024": "Dental 2025"})
    assert mapping.pairings["Dental 2024"] == "Dental 2025"
```

**Step 2: Install SDK and run failing tests**
Run: `uv add google-genai pydantic pytest`
Run: `uv run pytest tests/test_llm_diff.py`
Expected: FAIL "No module named llm_diff"

**Step 3: Define Pydantic Models in `llm_diff.py`**
```python
from pydantic import BaseModel
from typing import Dict, Optional, List, Any

class MappingReport(BaseModel):
    pairings: Dict[str, Optional[str]]

class ChangeReport(BaseModel):
    summary: str
    original_texts: str
    meta_data: Dict[str, Any]
```

**Step 4: Run test to verify it passes**
Run: `uv run pytest tests/test_llm_diff.py`
Expected: PASS

**Step 5: Commit**
```bash
git add pyproject.toml uv.lock tests/test_llm_diff.py llm_diff.py
git commit -m "feat: define pydantic schemas for gemini extractions"
```

---

### Task 2: Stage 1 - Structural Header Mapping

**Files:**
- Modify: `llm_diff.py`

**Step 1: Write mapping logic**
```python
import json
from google import genai

def map_headers(client: genai.Client, headers_24: List[str], headers_25: List[str]) -> MappingReport:
    prompt = f"Match the corresponding 2025 section to 2024. Return None if deleted.\n2024: {headers_24}\n2025: {headers_25}"
    response = client.models.generate_content(
        model='gemini-2.5-flash-lite',
        contents=prompt,
        config={'response_mime_type': 'application/json', 'response_schema': MappingReport}
    )
    return response.parsed
```

**Step 2: Commit**
```bash
git add llm_diff.py
git commit -m "feat: implement stage 1 fast semantic mapping via flash-lite"
```

---

### Task 3: Stage 2 - Asynchronous Parallel Gemini Extractions

**Files:**
- Modify: `llm_diff.py`

**Step 1: Write concurrent asynchronous handler**
```python
import asyncio

class DiffResult(BaseModel):
    changes: List[ChangeReport]

async def extract_changes_for_section(client_async, section_24_data: list, section_25_data: list) -> List[ChangeReport]:
    prompt = f"Extract numerical and meaningful benefit changes between these two datasets. Link back the exact meta_data from 2024 that corresponds to the change. \n2024 Data: {section_24_data}\n2025 Data: {section_25_data}"
    
    response = await client_async.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config={'response_mime_type': 'application/json', 'response_schema': DiffResult}
    )
    return response.parsed.changes

async def process_all_sections(client_async, mapping: MappingReport, data_24: dict, data_25: dict):
    tasks = []
    for h24, h25 in mapping.pairings.items():
        if h25:
            tasks.append(extract_changes_for_section(client_async, data_24[h24], data_25[h25]))
    
    results = await asyncio.gather(*tasks)
    
    flat_changes = []
    for r in results:
        flat_changes.extend(r)
    return flat_changes
```

**Step 2: Commit**
```bash
git add llm_diff.py
git commit -m "feat: deploy concurrent flash chunking logic via asyncio"
```

---

### Task 4: CLI Orchestration & Execution 

**Files:**
- Modify: `llm_diff.py`

**Step 1: Wire up the main pipeline loop**
```python
import sys

def main():
    with open("diff/changes_geom.json") as f:
        data = json.load(f)
    
    client = genai.Client()
    client_async = genai.Client(http_options={'api_version': 'v1alpha'}) # If leveraging alpha schema
    
    h24 = list(data["2024"].keys())
    h25 = list(data["2025"].keys())
    
    print("Stage 1: Mapping structure...")
    mapping = map_headers(client, h24, h25)
    
    print("Stage 2: Firing parallel context chunks...")
    final_changes = asyncio.run(process_all_sections(client_async, mapping, data["2024"], data["2025"]))
    
    with open("diff/final_contract_changes.json", "w") as f:
        json.dump([c.model_dump() for c in final_changes], f, indent=2)
    print("Saved exact differences to diff/final_contract_changes.json")

if __name__ == "__main__":
    main()
```

**Step 2: Commit**
```bash
git add llm_diff.py
git commit -m "feat: complete llm semantic mapper pipeline execution sequence"
```
