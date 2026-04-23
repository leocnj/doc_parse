import streamlit as st
import json
import fitz
import os
import ast

st.set_page_config(layout="wide", page_title="Benefit Changes Visualizer")

@st.cache_data
def load_data():
    if not os.path.exists("diff/changes_geom.json"):
        return None, None
    with open("diff/changes_geom.json") as f:
        geom_data = json.load(f)
        
    changes_data = []
    if os.path.exists("diff/final_contract_changes.json"):
        with open("diff/final_contract_changes.json") as f:
            changes_data = json.load(f)
            
    return geom_data, changes_data

def render_page_with_highlight(pdf_path, page_no, bbox):
    doc = fitz.open(pdf_path)
    page = doc.load_page(page_no - 1)
    
    origin = bbox.get("coord_origin", "BOTTOMLEFT")
    if origin == "BOTTOMLEFT":
        y_top = page.rect.height - bbox['t']
        y_bottom = page.rect.height - bbox['b']
    else:
        y_top = bbox['t']
        y_bottom = bbox['b']
        
    # Add a visual highlight rectangle padding
    pad = 5
    rect = fitz.Rect(bbox['l'] - pad, y_top - pad, bbox['r'] + pad, y_bottom + pad)
    
    # Draw a semi-transparent yellow rectangle over the table coordinates
    highlight = page.add_rect_annot(rect)
    highlight.set_colors(stroke=(1, 0.8, 0), fill=(1, 0.9, 0))
    highlight.set_opacity(0.4)
    highlight.update()
    
    # 1.5x zoom makes the text readable
    pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
    return pix.tobytes("png")

def main():
    st.title("Benefits Diff: 2024 vs 2025")
    st.markdown("Select an extracted section to visually verify changes against the original PDF representations.")
    
    data, ai_changes = load_data()
    if not data:
        st.warning("Geometric diff data not generated yet. Please run python diff_json.py.")
        return
        
    cat_2024 = data["2024"]
    cat_2025 = data["2025"]
    
    # Sidebar section selector
    st.sidebar.markdown("### Navigation")
    sections_24 = [k for k in cat_2024.keys() if cat_2024[k] and "table of contents" not in k.lower()]
    
    if not sections_24:
        st.error("No tables successfully extracted for 2024.")
        return
        
    def format_24(val):
        page = cat_2024[val][0]['prov'].get('page_no', '?')
        return f"{val} (Page {page})"
        
    selected_section_24 = st.sidebar.selectbox("2024 Table Category", sections_24, format_func=format_24)
    
    # Auto-match the closest 2025 header using simple word overlap 
    sections_25 = [k for k in cat_2025.keys() if cat_2025[k] and "table of contents" not in k.lower()]
    target_words = set(selected_section_24.lower().split())
    matching_25 = sorted(sections_25, key=lambda x: -len(set(x.lower().split()) & target_words))
    
    def format_25(val):
        page = cat_2025[val][0]['prov'].get('page_no', '?')
        return f"{val} (Page {page})"
        
    selected_section_25 = st.sidebar.selectbox("2025 Table Category", matching_25, format_func=format_25)
    
    tables_24 = cat_2024.get(selected_section_24, [])
    tables_25 = cat_2025.get(selected_section_25, [])
    
    # --- Top Panel: AI Insights ---
    st.subheader("🤖 AI Extracted Contract Changes")
    has_insights = False
    for t in tables_24:
        for c in ai_changes:
            raw_meta = c.get("meta_data", "{}").strip()
            if raw_meta.startswith("```"):
                raw_meta = "\n".join(raw_meta.split("\n")[1:-1])
            try:
                parsed_meta = ast.literal_eval(raw_meta)
            except Exception:
                try:
                    parsed_meta = json.loads(raw_meta.replace("'", '"'))
                except Exception:
                    parsed_meta = {}
                    
            target_meta = parsed_meta.get("prov", parsed_meta) if isinstance(parsed_meta, dict) else parsed_meta
                    
            if target_meta == t["prov"]:
                has_insights = True
                st.success(f"**Insight:** {c['summary']}")
                styled_text = c['original_texts']
                
                # Intelligent Markdown Table Preservation
                # Intelligent contrast rendering: split on || separator if present
                if " || " in styled_text:
                    parts = styled_text.split(" || ")
                    styled_lines = []
                    for part in parts:
                        part = part.strip()
                        if part.startswith("2024"):
                            styled_lines.append(f"🔴 **{part}**")
                        elif part.startswith("2025"):
                            styled_lines.append(f"🟢 **{part}**")
                        else:
                            styled_lines.append(part)
                    styled_text = "\n\n".join(styled_lines)
                elif "|---" not in styled_text.replace(" ", ""):
                    # Fallback: inline year tags with no table structure
                    styled_text = styled_text.replace("2024", "\n🔴 **2024**").replace("2025", "\n🟢 **2025**")
                
                st.info(f"**Original Extract Verification:**\n\n{styled_text}")
                
    if not has_insights:
        st.info("No comparative AI insights exist for this specific pairing.")
        
    st.markdown("---")
    st.subheader("📄 Base Structural Traces")
    
    # --- Bottom Panel: Raw Ground Truth Verification ---
    col1, col2 = st.columns(2)
    
    with col1:
        st.header(f"2024")
        for idx, t in enumerate(tables_24):
            with st.expander(f"Raw Markdown (Page {t['prov']['page_no']})", expanded=True):
                st.markdown(t["table_md"])
                st.markdown("---")
                if t["prov"]["page_no"]:
                    img = render_page_with_highlight("raw/molloy-univ-2024.pdf", t["prov"]["page_no"], t["prov"]["bbox"])
                    st.image(img, caption=f"2024 Source Capture", use_container_width=True)

    with col2:
        st.header(f"2025")
        for idx, t in enumerate(tables_25):
            with st.expander(f"Raw Markdown (Page {t['prov']['page_no']})", expanded=True):
                st.markdown(t["table_md"])
                st.markdown("---")
                if t["prov"]["page_no"]:
                    img = render_page_with_highlight("raw/molloy-univ-2025.pdf", t["prov"]["page_no"], t["prov"]["bbox"])
                    st.image(img, caption=f"2025 Source Capture", use_container_width=True)

if __name__ == "__main__":
    main()
