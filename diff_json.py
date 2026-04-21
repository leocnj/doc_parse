import json
from pathlib import Path
from docling_core.types.doc import DoclingDocument, SectionHeaderItem, TableItem

def parse_docling_json(file_path):
    doc = DoclingDocument.load_from_json(Path(file_path))
    
    sections = {}
    current_header = "Introduction"
    sections[current_header] = []
    
    for item, level in doc.iterate_items():
        if isinstance(item, SectionHeaderItem):
            current_header = item.text.strip()
            if current_header not in sections:
                sections[current_header] = []
        elif isinstance(item, TableItem):
            table_md = item.export_to_markdown(doc=doc)
            page_no = None
            bbox = None
            if item.prov:
                prov = item.prov[0]
                page_no = prov.page_no
                # PyMuPDF uses top-left origin (left, top, right, bottom). 
                # Docling's prov.bbox object normally provides l, t, r, b.
                # However, docling usually does bottom-up if origin is BOTTOMLEFT.
                # 't' technically represents the higher y-value. 
                # Given t > b in our test, we will just save the raw docling dict and adapt in app.py.
                bbox = {"l": prov.bbox.l, "t": prov.bbox.t, "r": prov.bbox.r, "b": prov.bbox.b, "coord_origin": prov.bbox.coord_origin.value if hasattr(prov.bbox.coord_origin, 'value') else "BOTTOMLEFT"}
            
            sections[current_header].append({
                "table_md": table_md,
                "prov": {
                    "page_no": page_no,
                    "bbox": bbox
                }
            })
            
    # filter out empty sections
    return {k: v for k, v in sections.items() if v}

def main():
    Path("diff").mkdir(exist_ok=True)
    
    cat_2024 = parse_docling_json("parsed/2024.json")
    cat_2025 = parse_docling_json("parsed/2025.json")
    
    diff_data = {"2024": cat_2024, "2025": cat_2025}

    with open("diff/changes_geom.json", "w", encoding="utf-8") as f:
        json.dump(diff_data, f, indent=2)
        
    print("Diff extraction complete. Output saved to diff/changes_geom.json")

if __name__ == "__main__":
    main()
