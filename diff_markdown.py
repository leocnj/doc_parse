import json
from pathlib import Path
import re

def parse_markdown_sections(file_path):
    sections = {}
    current_section = None
    content = ""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            match = re.match(r"^##\s+(.+)$", line)
            if match:
                if current_section:
                    sections[current_section] = content.strip()
                current_section = match.group(1).strip()
                content = ""
            else:
                if current_section:
                    content += line
                    
        if current_section:
            sections[current_section] = content.strip()
            
    return sections

def map_sections_to_categories(sections, year):
    categories = {
        "Medical": [],
        "Dental": [],
        "Vision": [],
        "Contributions": [],
        "Flexible Spending Account (FSA)": [],
        "Life & AD&D": [],
        "Long-Term Disability": [],
        "NYS DBL": [],
        "NYS PFL": [],
        "Aflac": [],
        "LegalShield": [],
        "EAP": [],
        "Retirement": [],
        "Commuter": []
    }
    
    for title, content in sections.items():
        title_up = title.upper()
        
        if "MEDICAL" in title_up or "ANTHEM" in title_up or "EMBLEM" in title_up or "AETNA PROGRAMS" in title_up or "AETNA HEALTH APP" in title_up or "DIFFERENCE CARD" in title_up:
            if "VISION" not in title_up and "DENTAL" not in title_up and "CONTRIBUTIONS" not in title_up:
                categories["Medical"].append({"title": title, "content": content})
                
        elif "DENTAL" in title_up:
            if "CONTRIBUTIONS" not in title_up:
                categories["Dental"].append({"title": title, "content": content})
                
        elif "VISION" in title_up:
            if "CONTRIBUTIONS" not in title_up:
                categories["Vision"].append({"title": title, "content": content})
                
        elif "CONTRIBUTIONS" in title_up:
            categories["Contributions"].append({"title": title, "content": content})
            
        elif "FLEXIBLE SPENDING" in title_up or "FSA" in title_up:
            categories["Flexible Spending Account (FSA)"].append({"title": title, "content": content})
            
        elif "LIFE AND ACCIDENTAL" in title_up or "LIFE INSURANCE" in title_up or "AD&D" in title_up:
            categories["Life & AD&D"].append({"title": title, "content": content})
            
        elif "LONG-TERM DISABILITY" in title_up or "LTD" in title_up:
            categories["Long-Term Disability"].append({"title": title, "content": content})
            
        elif "STATUTORY DISABILITY" in title_up or "DBL" in title_up:
            categories["NYS DBL"].append({"title": title, "content": content})
            
        elif "PAID FAMILY LEAVE" in title_up or "PFL" in title_up:
            categories["NYS PFL"].append({"title": title, "content": content})
            
        elif "AFLAC" in title_up:
            categories["Aflac"].append({"title": title, "content": content})
            
        elif "LEGALSHIELD" in title_up or "IDENTITY THEFT" in title_up:
            categories["LegalShield"].append({"title": title, "content": content})
            
        elif "EMPLOYEE ASSISTANCE" in title_up or "EAP" in title_up:
            categories["EAP"].append({"title": title, "content": content})
            
        elif "RETIREMENT" in title_up or "SRA" in title_up or "TIAA" in title_up:
            categories["Retirement"].append({"title": title, "content": content})
            
        elif "COMMUTER" in title_up:
            categories["Commuter"].append({"title": title, "content": content})
            
    return categories

def extract_tables(content):
    tables = []
    current_table = []
    in_table = False
    
    for line in content.split('\n'):
        if line.strip().startswith('|'):
            in_table = True
            current_table.append(line.strip())
        else:
            if in_table:
                tables.append('\n'.join(current_table))
                current_table = []
                in_table = False
                
    if in_table:
        tables.append('\n'.join(current_table))
        
    return tables

def main():
    Path("diff").mkdir(exist_ok=True)
    
    sections_2024 = parse_markdown_sections("parsed/2024.md")
    sections_2025 = parse_markdown_sections("parsed/2025.md")
    
    cat_2024 = map_sections_to_categories(sections_2024, 2024)
    cat_2025 = map_sections_to_categories(sections_2025, 2025)
    
    diff_data = {}
    
    for category in cat_2024.keys():
        diff_data[category] = {
            "2024": {
                "sections": [s["title"] for s in cat_2024[category]],
                "tables": []
            },
            "2025": {
                "sections": [s["title"] for s in cat_2025[category]],
                "tables": []
            }
        }
        
        for s in cat_2024[category]:
            tabs = extract_tables(s["content"])
            diff_data[category]["2024"]["tables"].extend(tabs)
            
        for s in cat_2025[category]:
            tabs = extract_tables(s["content"])
            diff_data[category]["2025"]["tables"].extend(tabs)

    with open("diff/changes.json", "w", encoding="utf-8") as f:
        json.dump(diff_data, f, indent=2)
        
    # Write summary 
    with open("diff/changes_summary.md", "w", encoding="utf-8") as f:
        f.write("# Employee Benefit Changes Summary (2024 vs 2025)\n\n")
        f.write("This document summarizes the presence of sections and tables across both years for each benefit category.\n\n")
        
        for cat, data in diff_data.items():
            f.write(f"## {cat}\n\n")
            
            f.write("### 2024\n")
            if data["2024"]["sections"]:
                f.write("**Sections Found:** \n- " + "\n- ".join(data["2024"]["sections"]) + "\n\n")
                f.write(f"**Tables Found:** {len(data['2024']['tables'])}\n\n")
                for t in data['2024']['tables']:
                    f.write(f"{t}\n\n")
            else:
                f.write("*No data found for 2024.*\n\n")
                
            f.write("### 2025\n")
            if data["2025"]["sections"]:
                f.write("**Sections Found:** \n- " + "\n- ".join(data["2025"]["sections"]) + "\n\n")
                f.write(f"**Tables Found:** {len(data['2025']['tables'])}\n\n")
                for t in data['2025']['tables']:
                    f.write(f"{t}\n\n")
            else:
                f.write("*No data found for 2025.*\n\n")
            f.write("---\n\n")

    print("Diff extraction complete. Output saved to diff/changes.json and diff/changes_summary.md")

if __name__ == "__main__":
    main()
