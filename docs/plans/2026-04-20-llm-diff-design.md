# LLM Semantic Diff via Gemini 2.5 Structured Output

## Overview
A pipeline stage that identifies benefit contract changes accurately using a two-stage LLM architecture. It sits between the geometric JSON tree generation (`diff_json.py`) and visual consumption in Streamlit (`app.py`).

## Requirements
* Consume `diff/changes_geom.json`
* Output highly granular semantic descriptions of benefit changes.
* Link each change directly back to bounding box and page geometry without sacrificing context.
* Prevent cross-domain hallucination via structural mapping.
* Run as efficiently as possible over the network.

## Architecture: Two-Stage Pipeline

### Stage 1: The Fast Mapper (`gemini-2.5-flash-lite`)
* **Role**: Structural Alignment.
* **Input**: An array of 2024 category labels and an array of 2025 category labels.
* **Logic**: Employs Pydantic `StructuredOutputs` to yield a strict 1:1 or 1:None mapping of matching sections, ensuring we never compare "Vision" with "General Disclosures" if the ordering shuffled.

### Stage 2: The Precise Extractor (`gemini-2.5-flash`)
* **Role**: Semantic numerical and textual extraction.
* **Execution**: Utilizes `asyncio.gather` for fully parallel concurrent inference against the Gemini API based on the mapped pairs from Stage 1.
* **Input**: The raw Markdown `table_md` representations corresponding to mapped headers.
* **Output**: A strict JSON schema managed by Pydantic:
  ```python
  class ChangeReport(BaseModel):
      summary: str           # "DMO Plan increased by $5"
      original_texts: str    # "DMO Plan: $50 -> $55"
      meta_data: list        # Passes through native Docling bbox + page_no exactly
  ```

## Dependencies
* `google-genai` (The officially supported new SDK)
* `pydantic`
* `asyncio`

## Expected Edge Cases
* **Missing Counterparts**: If a 2024 section vanished, the Mapper returns `None` and Stage 2 notes the plan removal without diffing.
* **Context Overload**: Bypassed entirely by Stage 2 executing chunk-based concurrent prompts rather than full-document injection.
