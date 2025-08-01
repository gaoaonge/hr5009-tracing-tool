#!/usr/bin/env python3
"""
Create pill-shaped badges for Original Amendments matching House Amendment style
"""

import pandas as pd
import re
import json

def load_original_amendment_data():
    """Load the original amendment data from amendment_cross_match_results.xlsx."""
    print("🔍 Loading Original Amendment data from amendment_cross_match_results.xlsx")
    
    try:
        # Load the amendment cross-match results
        df = pd.read_excel('amendment_cross_match_results.xlsx')
        print(f"Loaded {len(df)} original amendment records")
        
        # Create a lookup dictionary
        amendment_lookup = {}
        for _, row in df.iterrows():
            amendment_num = str(row.get('target_amendment_number', '')).strip()
            if amendment_num and amendment_num != 'nan':
                amendment_lookup[amendment_num] = {
                    'amendment_number': amendment_num,
                    'sponsor': str(row.get('target_sponsor', '')).strip(),
                    'source_section_title': str(row.get('source_section_title', '')).strip(),
                    'similarity_score': float(row.get('similarity_score', 0)),
                    'target_amendment_number': amendment_num
                }
        
        print(f"Created mapping for {len(amendment_lookup)} unique original amendments")
        return amendment_lookup
        
    except Exception as e:
        print(f"Error loading amendment data: {e}")
        return {}

def extract_original_amendments_from_html():
    """Extract Original Amendment information from existing HTML spans."""
    print("📄 Extracting Original Amendment data from HTML file")
    
    with open('ndaa_source_tracing_complete_enhanced_with_compact_house_rds.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Find all Original Amendment spans
    pattern = r'<span class="source-indicator source-original-amendment">Original Amendment Sec\. (\d+) proposed by (.+?)</span>'
    matches = re.findall(pattern, html_content)
    
    original_amendments = {}
    for section_num, sponsor in matches:
        if section_num not in original_amendments:
            original_amendments[section_num] = {
                'amendment_number': section_num,
                'section_number': section_num,
                'sponsor': sponsor,
                'title': f"Original Amendment Sec. {section_num}"
            }
    
    print(f"Extracted {len(original_amendments)} Original Amendment references from HTML")
    return original_amendments, html_content

def create_original_amendment_details_page(original_amendments):
    """Create a details page for Original Amendments."""
    
    # Convert mapping to JSON for JavaScript
    amendments_data = {}
    for section_num, amendment_info in original_amendments.items():
        amendments_data[section_num] = {
            'amendment_number': amendment_info['amendment_number'],
            'section_number': amendment_info['section_number'],
            'sponsor': amendment_info['sponsor'],
            'title': amendment_info['title']
        }
    
    details_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Original Amendment Details</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 2rem;
            background: linear-gradient(135deg, #ff6b35 0%, #f7931e 100%);
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
            background: linear-gradient(135deg, #ff6b35, #f7931e);
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
            border-left: 4px solid #ff6b35;
        }}
        .info-label {{
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 0.5rem;
        }}
        .back-button {{
            display: inline-block;
            background: linear-gradient(135deg, #ff6b35, #f7931e);
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
            <h1><i class="fas fa-scroll"></i> Original Amendment Details</h1>
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
                        <p>The requested Original Amendment ${{amendmentNumber || 'N/A'}} could not be found.</p>
                    </div>
                `;
                return;
            }}
            
            const amendment = amendmentsData[amendmentNumber];
            
            detailsContainer.innerHTML = `
                <h2><i class="fas fa-file-alt"></i> Original Amendment Sec. ${{amendmentNumber}}</h2>
                
                <div class="info-section">
                    <div class="info-label">Amendment Section:</div>
                    <div>Section ${{amendment.section_number}}</div>
                </div>
                
                <div class="info-section">
                    <div class="info-label">Sponsor:</div>
                    <div>${{amendment.sponsor}}</div>
                </div>
                
                <div class="info-section">
                    <div class="info-label">Amendment Title:</div>
                    <div>${{amendment.title}}</div>
                </div>
                
                <div class="info-section">
                    <div class="info-label">Description:</div>
                    <div>This section originated from an original Senate amendment proposed by ${{amendment.sponsor}}.</div>
                </div>
            `;
        }}
        
        // Load amendment details when page loads
        document.addEventListener('DOMContentLoaded', displayAmendmentDetails);
    </script>
</body>
</html>
    """
    
    with open('original_amendment_details.html', 'w', encoding='utf-8') as f:
        f.write(details_html)
    
    print("📄 Created original_amendment_details.html for viewing amendment details")

def create_original_amendment_badge(amendment_info):
    """Create HTML for pill-shaped Original Amendment badge."""
    
    return f"""
                <div style="position: relative; margin-left: 2rem; margin-top: 0.5rem;">
                    <!-- Branching connector line -->
                    <div style="position: absolute; top: 0; left: -2rem; width: 1.5rem; height: 1px; 
                               background: linear-gradient(to right, #3498db, #ff6b35); margin-top: 1rem;"></div>
                    <div style="position: absolute; top: 0; left: -0.5rem; width: 1px; height: 1rem; 
                               background: linear-gradient(to bottom, #3498db, #ff6b35);"></div>
                    
                    <!-- Simple clickable Original Amendment badge -->
                    <a href="original_amendment_details.html?amendment={amendment_info['amendment_number']}" 
                       target="_blank" style="text-decoration: none;">
                        <div style="background: linear-gradient(135deg, #ff6b35, #f7931e); color: white; 
                                   padding: 0.4rem 1rem; border-radius: 25px; font-size: 0.9em; font-weight: 600;
                                   box-shadow: 0 2px 4px rgba(0,0,0,0.1); border: none;
                                   cursor: pointer; transition: all 0.3s ease; display: inline-flex; align-items: center;
                                   min-height: 2.2rem;"
                             onmouseover="this.style.transform='scale(1.05)'"
                             onmouseout="this.style.transform='scale(1)'">
                            
                            <!-- Simple badge content -->
                            <div style="display: flex; align-items: center;">
                                <i class="fas fa-scroll" style="margin-right: 0.5rem;"></i> 
                                Original Amendment {amendment_info['amendment_number']}
                            </div>
                        </div>
                    </a>
                </div>"""

def replace_original_amendment_spans(html_content, original_amendments):
    """Replace Original Amendment spans with pill-shaped badges."""
    
    enhanced_count = 0
    
    # Pattern to match the Original Amendment spans
    pattern = r'<span class="source-indicator source-original-amendment">Original Amendment Sec\. (\d+) proposed by (.+?)</span>'
    
    def replace_span(match):
        nonlocal enhanced_count
        section_num = match.group(1)
        sponsor = match.group(2)
        
        if section_num in original_amendments:
            enhanced_count += 1
            return create_original_amendment_badge(original_amendments[section_num])
        else:
            return match.group(0)  # Return original if not found
    
    enhanced_content = re.sub(pattern, replace_span, html_content)
    
    print(f"Enhanced {enhanced_count} Original Amendment spans with pill badges")
    return enhanced_content

def main():
    """Main function to enhance Original Amendments."""
    
    print("🔍 Creating Original Amendment pill badges")
    print("📦 Converting inline spans to clickable pill badges")
    
    # Extract existing Original Amendment data from HTML
    original_amendments, html_content = extract_original_amendments_from_html()
    
    if not original_amendments:
        print("❌ No Original Amendments found in HTML file")
        return
    
    # Create the Original Amendment details page
    create_original_amendment_details_page(original_amendments)
    
    # Replace spans with pill badges
    enhanced_content = replace_original_amendment_spans(html_content, original_amendments)
    
    # Save the enhanced HTML
    output_file = 'ndaa_source_tracing_complete_enhanced_with_compact_house_rds.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(enhanced_content)
    
    print(f"\n✅ Original Amendment enhancement complete!")
    print(f"📄 Output file: {output_file}")
    print(f"🔗 View at: http://localhost:8020/{output_file}")
    print(f"💡 Click on orange Original Amendment badges to open details in new page!")
    print(f"📋 Details page: original_amendment_details.html")

if __name__ == "__main__":
    main() 