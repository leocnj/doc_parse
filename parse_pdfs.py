from pathlib import Path
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableStructureOptions, TableFormerMode
from docling.datamodel.accelerator_options import AcceleratorOptions, AcceleratorDevice
from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn, TextColumn
from rich.console import Console

console = Console()

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
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=console,
        transient=False,
    ) as progress:
        task = progress.add_task(f"[cyan]Parsing {pdf_path.name} (Extracting layout and tables)...", total=None)
        
        result = converter.convert(pdf_path)
        md_text = result.document.export_to_markdown()
        progress.update(task, completed=100, description=f"[green]Successfully parsed {pdf_path.name}![/green]")

    out_file = OUT_DIR / f"{year}.md"
    out_file.write_text(md_text, encoding="utf-8")
    console.print(f"  [bold green]✓[/bold green] Saved → [yellow]{out_file}[/yellow] ({len(md_text):,} chars)\n")

console.print("[bold cyan]All done.[/bold cyan]")
