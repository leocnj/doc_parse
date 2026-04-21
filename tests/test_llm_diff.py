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
