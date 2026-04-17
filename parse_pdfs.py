from pathlib import Path
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableStructureOptions, TableFormerMode
from docling.datamodel.accelerator_options import AcceleratorOptions, AcceleratorDevice

# ── CPU-only configuration ──────────────────────────────────────────────────
cpu_options = AcceleratorOptions(
    device=AcceleratorDevice.CPU,
    num_threads=4,  # tune to your CPU core count (check with: nproc)
)

table_options = TableStructureOptions(mode=TableFormerMode.ACCURATE)

pipeline_options = PdfPipelineOptions(
    accelerator_options=cpu_options,
    do_ocr=False,           # PDFs are digital — skip OCR to save time
    do_table_structure=True, # Enable TableFormer for accurate table parsing
    table_structure_options=table_options,
)

converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)

# ── Parse both PDFs ─────────────────────────────────────────────────────────
RAW_DIR = Path("raw")
OUT_DIR = Path("parsed")
OUT_DIR.mkdir(exist_ok=True)

for pdf_path in sorted(RAW_DIR.glob("*.pdf")):
    year = pdf_path.stem.split("-")[-1]  # e.g. "2024", "2025"
    print(f"\nParsing {pdf_path.name} (this may take 5–15 min on CPU)...")

    result = converter.convert(pdf_path)
    md_text = result.document.export_to_markdown()

    out_file = OUT_DIR / f"{year}.md"
    out_file.write_text(md_text, encoding="utf-8")
    print(f"  ✓ Saved → {out_file}  ({len(md_text):,} chars)")

print("\nAll done.")
