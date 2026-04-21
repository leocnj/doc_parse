import streamlit as st
import json
import fitz
import os

st.set_page_config(layout="wide", page_title="Benefit Changes Visualizer")

@st.cache_data
def load_data():
    if not os.path.exists("diff/changes_geom.json"):
        return None
    with open("diff/changes_geom.json") as f:
        return json.load(f)

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
    
    data = load_data()
    if not data:
        st.warning("Geometric diff data not generated yet. Please run python diff_json.py.")
        return
        
    cat_2024 = data["2024"]
    cat_2025 = data["2025"]
    
    # Sidebar section selector
    st.sidebar.markdown("### Navigation")
    sections_24 = [k for k in cat_2024.keys() if cat_2024[k]]
    
    if not sections_24:
        st.error("No tables successfully extracted for 2024.")
        return
        
    selected_section_24 = st.sidebar.selectbox("2024 Table Category", sections_24)
    
    # Auto-match the closest 2025 header using simple word overlap 
    sections_25 = [k for k in cat_2025.keys() if cat_2025[k]]
    target_words = set(selected_section_24.lower().split())
    matching_25 = sorted(sections_25, key=lambda x: -len(set(x.lower().split()) & target_words))
    selected_section_25 = st.sidebar.selectbox("2025 Table Category", matching_25)
    
    # Layout Content
    col1, col2 = st.columns(2)
    
    # Left Column - 2024
    with col1:
        st.header(f"2024: {selected_section_24}")
        tables = cat_2024.get(selected_section_24, [])
        for idx, t in enumerate(tables):
            with st.expander(f"Data Origin: Page {t['prov']['page_no']}", expanded=True):
                # Render the raw markdown data underneath
                st.markdown(t["table_md"])
                st.markdown("---")
                if t["prov"]["page_no"]:
                    img = render_page_with_highlight("raw/molloy-univ-2024.pdf", t["prov"]["page_no"], t["prov"]["bbox"])
                    st.image(img, caption=f"2024 Source Bounding Box (Page {t['prov']['page_no']})", use_column_width=True)

    # Right Column - 2025
    with col2:
        st.header(f"2025: {selected_section_25}")
        tables = cat_2025.get(selected_section_25, [])
        for idx, t in enumerate(tables):
            with st.expander(f"Data Origin: Page {t['prov']['page_no']}", expanded=True):
                st.markdown(t["table_md"])
                st.markdown("---")
                if t["prov"]["page_no"]:
                    img = render_page_with_highlight("raw/molloy-univ-2025.pdf", t["prov"]["page_no"], t["prov"]["bbox"])
                    st.image(img, caption=f"2025 Source Bounding Box (Page {t['prov']['page_no']})", use_column_width=True)

if __name__ == "__main__":
    main()
