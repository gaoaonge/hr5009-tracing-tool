#!/usr/bin/env python3
"""
Script to create compact House Amendment badges that expand on click.
Shows only "House Amendment Sec. xxx" initially, with details hidden until clicked.
"""

import pandas as pd
import re
import json

def load_data():
    """Load and process the Excel data files."""
    
    # Load the header matching data from the 'Matched' sheet
    matched_df = pd.read_excel('header_match_results_high_quality.xlsx', sheet_name='Matched')
    
    # Load the HR8070 amendments data
    hr8070_df = pd.read_excel('HR8070_amendments_with_sponsors_FINAL.xlsx')
    
    print(f"Loaded {len(matched_df)} matched headers from header_match_results_high_quality.xlsx")
    print(f"Loaded {len(hr8070_df)} HR8070 amendments")
    
    return matched_df, hr8070_df

def extract_section_number(text):
    """Extract numeric section number from text like 'SEC. 723.'"""
    if pd.isna(text):
        return None
    match = re.search(r'(\d+)', str(text))
    return int(match.group(1)) if match else None

def create_house_rds_mapping(matched_df, hr8070_df):
    """Create mapping from House RDS section numbers to amendment information."""
    
    # Extract section numbers from the matched_bill_section_number column
    matched_df['section_number'] = matched_df['matched_bill_section_number'].apply(extract_section_number)
    
    # Create mapping dictionary
    house_rds_mapping = {}
    
    for _, row in matched_df.iterrows():
        section_num = row['section_number']
        if pd.isna(section_num):
            continue
            
        amendment_num = row['amendment_number']
        
        # Find corresponding HR8070 data
        hr8070_match = hr8070_df[hr8070_df['individual_amendment_number'] == amendment_num]
        
        if not hr8070_match.empty:
            hr8070_row = hr8070_match.iloc[0]
            
            # Get sponsor information
            sponsors = str(row.get('Sponsors', 'Unknown')).strip()
            if sponsors in ['', 'nan', 'None']:
                sponsors = str(hr8070_row.get('Sponsor', 'Unknown')).strip()
            
            mapping_info = {
                'house_rds_section': section_num,
                'amendment_number': amendment_num,
                'hml_section_title': str(row['hml_section_title']).strip(),
                'matched_bill_section_title': str(row['matched_bill_section_title']).strip(),
                'sponsors': sponsors,
                'vote_type': str(row.get('vote_type', '')).strip(),
                'yea': str(row.get('yea', '')).strip(),
                'nay': str(row.get('nay', '')).strip(),
                'agreed_or_not': str(row.get('agrred_or_not', '')).strip(),
                'similarity_score': float(row.get('similarity_score', 0)),
                'hml_full_content': str(hr8070_row.get('hml_full_content', '')).strip()
            }
            
            house_rds_mapping[section_num] = mapping_info
    
    print(f"Created mapping for {len(house_rds_mapping)} House RDS sections")
    return house_rds_mapping

def create_house_amendment_details_page(house_rds_mapping):
    """Create a details page that shows House Amendment information based on URL parameters."""
    
    # Convert mapping to JSON for JavaScript
    import json
    amendments_data = {}
    for section_num, mapping_info in house_rds_mapping.items():
        amendments_data[mapping_info['amendment_number']] = {
            'amendment_number': mapping_info['amendment_number'],
            'hml_section_title': mapping_info['hml_section_title'],
            'sponsors': mapping_info['sponsors'],
            'vote_type': mapping_info['vote_type'],
            'yea': mapping_info['yea'],
            'nay': mapping_info['nay'],
            'agreed_or_not': mapping_info['agreed_or_not'],
            'hml_full_content': mapping_info['hml_full_content']
        }
    
    details_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>House Amendment Details</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 2rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #8e44ad, #3498db);
            color: white;
            padding: 2rem;
            text-align: center;
        }}
        .content {{
            padding: 2rem;
        }}
        .info-section {{
            margin-bottom: 1.5rem;
            padding: 1rem;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #3498db;
        }}
        .info-label {{
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 0.5rem;
        }}
        .full-text {{
            background: #f1f2f6;
            padding: 1.5rem;
            border-radius: 8px;
            white-space: pre-wrap;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            line-height: 1.5;
            max-height: 400px;
            overflow-y: auto;
            border: 1px solid #ddd;
        }}
        .back-button {{
            display: inline-block;
            background: linear-gradient(135deg, #3498db, #8e44ad);
            color: white;
            padding: 0.75rem 1.5rem;
            border-radius: 8px;
            text-decoration: none;
            font-weight: bold;
            margin-bottom: 1rem;
            transition: all 0.3s ease;
        }}
        .back-button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }}
        .error {{
            text-align: center;
            padding: 2rem;
            color: #e74c3c;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1><i class="fas fa-code-branch"></i> House Amendment Details</h1>
        </div>
        <div class="content">
                         <a href="ndaa_source_tracing_complete_enhanced_with_compact_house_rds.html" class="back-button">
                 <i class="fas fa-arrow-left"></i> Back to NDAA Source Tracing
             </a>
            <div id="amendment-details">
                <div class="error">
                    <h2>Loading Amendment Details...</h2>
                    <p>Please wait while we load the amendment information.</p>
                </div>
            </div>
        </div>
    </div>

    <script>
        const amendmentsData = {json.dumps(amendments_data, indent=2)};
        
        function getUrlParameter(name) {{
            const urlParams = new URLSearchParams(window.location.search);
            return urlParams.get(name);
        }}
        
        function displayAmendmentDetails() {{
            const amendmentNumber = getUrlParameter('amendment');
            const detailsContainer = document.getElementById('amendment-details');
            
            if (!amendmentNumber || !amendmentsData[amendmentNumber]) {{
                detailsContainer.innerHTML = `
                    <div class="error">
                        <h2>Amendment Not Found</h2>
                        <p>The requested House Amendment ${{amendmentNumber || 'N/A'}} could not be found.</p>
                    </div>
                `;
                return;
            }}
            
            const amendment = amendmentsData[amendmentNumber];
            
            let sponsorsSection = '';
            if (amendment.sponsors && amendment.sponsors !== 'Unknown' && amendment.sponsors !== '') {{
                sponsorsSection = `
                    <div class="info-section">
                        <div class="info-label">Sponsors:</div>
                        <div>${{amendment.sponsors}}</div>
                    </div>
                `;
            }}
            
            let voteSection = '';
            if (amendment.vote_type && amendment.vote_type !== '') {{
                voteSection = `
                    <div class="info-section">
                        <div class="info-label">Vote Information:</div>
                        <div><strong>Type:</strong> ${{amendment.vote_type}}</div>
                        <div><strong>Yea:</strong> ${{amendment.yea || 'N/A'}}, <strong>Nay:</strong> ${{amendment.nay || 'N/A'}}</div>
                        <div><strong>Result:</strong> ${{amendment.agreed_or_not || 'N/A'}}</div>
                    </div>
                `;
            }}
            
            let fullTextSection = '';
            if (amendment.hml_full_content && amendment.hml_full_content !== '') {{
                fullTextSection = `
                    <div class="info-section">
                        <div class="info-label">Full Amendment Text:</div>
                        <div class="full-text">${{amendment.hml_full_content}}</div>
                    </div>
                `;
            }}
            
            detailsContainer.innerHTML = `
                <h2><i class="fas fa-file-alt"></i> House Amendment ${{amendmentNumber}}</h2>
                
                <div class="info-section">
                    <div class="info-label">Amendment Title:</div>
                    <div>${{amendment.hml_section_title}}</div>
                </div>
                
                ${{sponsorsSection}}
                ${{voteSection}}
                ${{fullTextSection}}
            `;
        }}
        
        // Load amendment details when page loads
        document.addEventListener('DOMContentLoaded', displayAmendmentDetails);
    </script>
</body>
</html>
    """
    
    with open('house_amendment_details.html', 'w', encoding='utf-8') as f:
        f.write(details_html)
    
    print("📄 Created house_amendment_details.html for viewing amendment details")

def create_compact_branching_house_rds_badge(mapping_info):
    """Create HTML for simple clickable House RDS badge that opens details in new page."""
    
    # Create a simple branching badge that links to details page
    badge_html = f"""
                <div style="position: relative; margin-left: 2rem; margin-top: 0.5rem;">
                    <!-- Branching connector line -->
                    <div style="position: absolute; top: 0; left: -2rem; width: 1.5rem; height: 1px; 
                               background: linear-gradient(to right, #3498db, #8e44ad); margin-top: 1rem;"></div>
                    <div style="position: absolute; top: 0; left: -0.5rem; width: 1px; height: 1rem; 
                               background: linear-gradient(to bottom, #3498db, #8e44ad);"></div>
                    
                    <!-- Simple clickable House Amendment badge -->
                    <a href="house_amendment_details.html?amendment={mapping_info['amendment_number']}" 
                       target="_blank" style="text-decoration: none;">
                        <div style="background: linear-gradient(135deg, #8e44ad, #3498db); color: white; 
                                   padding: 0.4rem 1rem; border-radius: 25px; font-size: 0.9em; font-weight: 600;
                                   box-shadow: 0 2px 4px rgba(0,0,0,0.1); border: none;
                                   cursor: pointer; transition: all 0.3s ease; display: inline-flex; align-items: center;
                                   min-height: 2.2rem;"
                             onmouseover="this.style.transform='scale(1.05)'"
                             onmouseout="this.style.transform='scale(1)'">
                            
                            <!-- Simple badge content -->
                            <div style="display: flex; align-items: center;">
                                <i class="fas fa-code-branch" style="margin-right: 0.5rem;"></i> 
                                House Amendment {mapping_info['amendment_number']}
                            </div>
                        </div>
                    </a>
                </div>"""
    
    return badge_html

def enhance_static_html_with_compact_branching(house_rds_mapping):
    """Enhance the static HTML file with compact branching House RDS information."""
    
    with open('ndaa_source_tracing_complete_enhanced.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # No JavaScript functions needed for simple links
    toggle_functions = """
    <script>
    function toggleFullText(elementId) {
        const element = document.getElementById(elementId);
        if (element.style.display === 'none' || element.style.display === '') {
            element.style.display = 'block';
        } else {
            element.style.display = 'none';
        }
    }
    </script>"""
    
    # Add the toggle functions before closing body tag
    html_content = html_content.replace('</body>', toggle_functions + '\n</body>')
    
    # Find and enhance sections with House RDS references
    enhanced_count = 0
    
    # Enhanced pattern to specifically target House RDS badges and insert branching content after them
    def enhance_house_rds_section(match):
        nonlocal enhanced_count
        
        full_match = match.group(0)
        
        # Look for House RDS section number in the content
        section_num_matches = re.findall(r'House RDS Sec\.\s*(\d+)', full_match)
        
        if section_num_matches:
            for section_num_str in section_num_matches:
                section_num = int(section_num_str)
                
                if section_num in house_rds_mapping:
                    mapping_info = house_rds_mapping[section_num]
                    house_rds_badge = create_compact_branching_house_rds_badge(mapping_info)
                    
                    # Insert the branching badge right after the House RDS badge
                    # Look for the House RDS badge specifically and add after it
                    house_rds_pattern = f'(House RDS Sec\\. {section_num}[^<]*</[^>]+>)'
                    
                    def add_branch(rds_match):
                        return rds_match.group(0) + house_rds_badge
                    
                    full_match = re.sub(house_rds_pattern, add_branch, full_match, flags=re.IGNORECASE)
                    enhanced_count += 1
                    break  # Only enhance once per section
        
        return full_match
    
    # Pattern to match larger blocks that might contain House RDS sections
    # This pattern captures trace cards or similar containers
    pattern = r'(<div[^>]*>.*?House RDS Sec\.\s*\d+.*?</div>(?:\s*<div[^>]*>.*?</div>)*)'
    
    html_content = re.sub(pattern, enhance_house_rds_section, html_content, flags=re.DOTALL | re.IGNORECASE)
    
    # Save the enhanced HTML
    output_file = 'ndaa_source_tracing_complete_enhanced_with_compact_house_rds.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Enhanced {enhanced_count} sections with simple House RDS badges")
    print(f"Updated HTML saved as: {output_file}")
    return output_file

def main():
    """Main function."""
    
    print("🔍 Using header_match_results_high_quality.xlsx 'Matched' sheet for matching")
    print("📦 Creating simple clickable House Amendment badges")
    
    # Load data
    matched_df, hr8070_df = load_data()
    
    # Create House RDS mapping
    house_rds_mapping = create_house_rds_mapping(matched_df, hr8070_df)
    
    # Create the House Amendment details page
    create_house_amendment_details_page(house_rds_mapping)
    
    # Enhance static HTML with compact branching layout
    output_file = enhance_static_html_with_compact_branching(house_rds_mapping)
    
    print(f"\n✅ Simple clickable House RDS enhancement complete!")
    print(f"📄 Output file: {output_file}")
    print(f"🔗 View at: http://localhost:8020/{output_file}")
    print(f"📊 Data source: header_match_results_high_quality.xlsx (Matched sheet)")
    print(f"💡 Click on House Amendment badges to open details in new page!")
    print(f"📋 Details page: house_amendment_details.html")

if __name__ == "__main__":
    main() 