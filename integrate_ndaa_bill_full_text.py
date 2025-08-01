#!/usr/bin/env python3

import pandas as pd
import re
import json

def load_ndaa_bill_data():
    """Load the NDAA Bill References Excel file with full_text column"""
    try:
        df = pd.read_excel('NDAA_Bill_References_V5_with_text (6).xlsx')
        print(f"Loaded NDAA Bill data with {len(df)} rows")
        print(f"Columns: {df.columns.tolist()}")
        return df
    except Exception as e:
        print(f"Error loading NDAA Bill data: {e}")
        return None

def extract_section_number(header):
    """Extract section number from header text"""
    # Look for patterns like "Sec. 101", "SEC. 101", "Section 101"
    patterns = [
        r'SEC?\.\s*(\d+)',
        r'Section\s+(\d+)',
        r'Sec\s+(\d+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, header, re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None

def create_section_mapping(df):
    """Create mapping from section numbers to full_text content"""
    section_mapping = {}
    
    for _, row in df.iterrows():
        header = str(row.get('header', ''))
        full_text = str(row.get('full_text', ''))
        section_index = row.get('section_index', '')
        
        # Extract section number from header
        section_num = extract_section_number(header)
        
        if section_num and full_text and full_text != 'nan':
            # Clean up the full_text for display
            clean_text = full_text.strip()
            if len(clean_text) > 500:
                # Truncate very long text but keep it meaningful
                clean_text = clean_text[:500] + "..."
            
            section_mapping[section_num] = {
                'header': header,
                'full_text': clean_text,
                'section_index': section_index
            }
            print(f"Mapped Section {section_num}: {header[:50]}...")
    
    print(f"Created mapping for {len(section_mapping)} sections")
    return section_mapping

def update_html_with_dynamic_diff_note(input_file, output_file, section_mapping):
    """Update HTML to use dynamic diff-note content"""
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # First, embed the section mapping data in the JavaScript
    mapping_js = f"const sectionFullTextMapping = {json.dumps(section_mapping, indent=2)};"
    
    # Find where to insert the mapping data (after tracesData declaration)
    traces_pattern = r'(let tracesData = \[.*?\];)'
    if re.search(traces_pattern, content, re.DOTALL):
        content = re.sub(
            traces_pattern,
            r'\1\n\n        // Section full text mapping from NDAA_Bill xlsx\n        ' + mapping_js,
            content,
            flags=re.DOTALL
        )
    
    # Replace the static diff-note with a dynamic one
    old_diff_note = r'<div class="diff-note">\s*<strong>Compare:</strong>[^<]*</div>'
    new_diff_note = '''<div class="diff-note" id="dynamic-diff-note">
                    <strong>Section Content:</strong> <span id="section-full-text">Loading section content...</span>
                </div>'''
    
    content = re.sub(old_diff_note, new_diff_note, content, flags=re.DOTALL)
    
    # Update the openTraceModal function to populate the diff-note
    open_modal_pattern = r'(function openTraceModal\(trace\) \{[^}]*?)(\s*document\.getElementById\(\'trace-modal\'\)\.classList\.add\(\'active\'\);)'
    
    update_diff_note_code = '''
            // Update diff-note with section-specific content
            updateDiffNote(trace);
'''
    
    content = re.sub(
        open_modal_pattern,
        r'\1' + update_diff_note_code + r'\2',
        content,
        flags=re.DOTALL
    )
    
    # Add the updateDiffNote function
    update_function = '''
        function updateDiffNote(trace) {
            const diffNoteElement = document.getElementById('section-full-text');
            if (!diffNoteElement) return;
            
            // Extract section number from trace header
            const sectionPattern = new RegExp('SEC?\\\\\.\\\\s+(\\\\d+)', 'i');
            const sectionMatch = trace.section_header.match(sectionPattern);
            if (sectionMatch) {
                const sectionNum = parseInt(sectionMatch[1]);
                const sectionData = sectionFullTextMapping[sectionNum];
                
                if (sectionData && sectionData.full_text) {
                    diffNoteElement.textContent = sectionData.full_text;
                } else {
                    diffNoteElement.textContent = "No detailed content available for Section " + sectionNum + ".";
                }
            } else {
                // If no section number found, try to match by header
                const headerText = trace.section_header.toLowerCase();
                let foundContent = null;
                
                for (const [sectionNum, data] of Object.entries(sectionFullTextMapping)) {
                    if (data.header.toLowerCase().includes(headerText.substring(0, 30))) {
                        foundContent = data.full_text;
                        break;
                    }
                }
                
                if (foundContent) {
                    diffNoteElement.textContent = foundContent;
                } else {
                    diffNoteElement.textContent = "This shows the referenced source text compared with the final NDAA H.R. 5009 ENR text.";
                }
            }
        }
'''
    
    # Insert the function before the closing script tag
    content = re.sub(
        r'(\s*</script>\s*</body>)',
        update_function + r'\1',
        content
    )
    
    # Write the updated content
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Updated HTML saved to {output_file}")

def main():
    # Load the NDAA Bill data
    df = load_ndaa_bill_data()
    if df is None:
        return
    
    # Create section mapping
    section_mapping = create_section_mapping(df)
    
    if not section_mapping:
        print("No section mapping created. Check the data structure.")
        return
    
    # Update the main HTML file
    input_file = 'ndaa_source_tracing_WITH_ORIGINAL_AMENDMENT_BADGES.html'
    output_file = 'ndaa_source_tracing_WITH_DYNAMIC_FULL_TEXT.html'
    
    update_html_with_dynamic_diff_note(input_file, output_file, section_mapping)
    
    print(f"\nCompleted! The updated interface with dynamic full text is available at:")
    print(f"http://localhost:8020/{output_file}")

if __name__ == "__main__":
    main() 