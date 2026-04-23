from pydantic import BaseModel
from typing import Dict, Optional, Any, List
import asyncio

class MappingPair(BaseModel):
    head_2024: str
    head_2025: Optional[str]

class MappingReport(BaseModel):
    pairings: List[MappingPair]

class ChangeReport(BaseModel):
    summary: str
    original_texts: str
    meta_data: str

class DiffResult(BaseModel):
    changes: List[ChangeReport]

def map_headers(client, headers_24: List[str], headers_25: List[str]) -> MappingReport:
    prompt = f"Match the corresponding 2025 section to 2024. Return None if deleted.\n2024: {headers_24}\n2025: {headers_25}"
    response = client.models.generate_content(
        model='gemini-2.5-flash-lite',
        contents=prompt,
        config={'response_mime_type': 'application/json', 'response_schema': MappingReport}
    )
    return response.parsed

async def process_all_sections(client_async, mapping: MappingReport, data_24: dict, data_25: dict):
    sem = asyncio.Semaphore(3)
    
    async def extract_changes_for_section(client_async, section_24_data: list, section_25_data: list) -> List[ChangeReport]:
        async with sem:
            prompt = (
                f"Extract all numerical and meaningful benefit changes between these two datasets.\n"
                f"For each change, write `original_texts` as a single string containing BOTH the 2024 source excerpt AND the 2025 source excerpt, "
                f"separated by ' || ' (double pipe). Always prefix each side with '2024:' and '2025:' labels.\n"
                f"Example: '2024: | DPPO | $16.60 | || 2025: | DPPO | $17.45 |'\n"
                f"Link back the exact meta_data from 2024 that corresponds to the change.\n"
                f"2024 Data: {section_24_data}\n2025 Data: {section_25_data}"
            )
            
            try:
                response = await client_async.aio.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                    config={'response_mime_type': 'application/json', 'response_schema': DiffResult}
                )
                return response.parsed.changes
            except Exception as e:
                print(f"Error extracting section: {e}")
                return []

    tasks = []
    for pair in mapping.pairings:
        if pair.head_2025 and pair.head_2025 in data_25 and pair.head_2024 in data_24:
            tasks.append(extract_changes_for_section(client_async, data_24[pair.head_2024], data_25[pair.head_2025]))
    
    from tqdm.asyncio import tqdm
    results = await tqdm.gather(*tasks, desc=f"Extracting {len(tasks)} LLM Chunks", colour="CYAN")
    
    flat_changes = []
    for r in results:
        flat_changes.extend(r)
    return flat_changes

def main():
    import json
    import asyncio
    from google import genai
    from dotenv import load_dotenv
    
    load_dotenv()
    
    with open("diff/changes_geom.json") as f:
        data = json.load(f)
    
    client = genai.Client()
    client_async = genai.Client(http_options={'api_version': 'v1alpha'}) # If leveraging alpha schema
    
    h24 = list(data["2024"].keys())
    h25 = list(data["2025"].keys())
    
    print("Stage 1: Mapping structure...")
    mapping = map_headers(client, h24, h25)
    valid_pairs = sum(1 for p in mapping.pairings if p.head_2025)
    print(f"  ✓ Mapped {valid_pairs} structural sections across both years:")
    for pair in mapping.pairings:
        if pair.head_2025:
            print(f"    - [2024] '{pair.head_2024}' -> [2025] '{pair.head_2025}'")
        else:
            print(f"    - [2024] '{pair.head_2024}' -> [2025] (Deleted)")
    
    print("Stage 2: Firing parallel context chunks...")
    final_changes = asyncio.run(process_all_sections(client_async, mapping, data["2024"], data["2025"]))
    
    with open("diff/final_contract_changes.json", "w") as f:
        json.dump([c.model_dump() for c in final_changes], f, indent=2)
    print("Saved exact differences to diff/final_contract_changes.json")

if __name__ == "__main__":
    main()
