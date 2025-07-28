#!/usr/bin/env python3
"""
Content-Focused Diff Website
Diff tool that ignores spacing/formatting and focuses on meaningful content changes
"""

import json
import os
import pandas as pd
import threading
import time
import webbrowser
import http.server
import socketserver
import re

def load_ih_to_rh_traces():
    """Load only IH→RH traces"""
    print("Loading IH→RH traces...")
    
    # Load Excel files
    ih_df = pd.read_excel('HR8070-ih-sections.xlsx')
    rh_df = pd.read_excel('HR8070-rh-sections.xlsx')
    
    print(f"✅ Loaded {len(ih_df)} IH sections")
    print(f"✅ Loaded {len(rh_df)} RH sections")
    
    # Load matching file
    ih_to_rh_df = pd.read_excel('HR8070_Section_Title_Matches.xlsx')
    
    print(f"✅ Loaded {len(ih_to_rh_df)} IH→RH matches")
    
    # Create lookup dictionary for high-confidence matches (≥90%)
    ih_to_rh_lookup = {}
    for _, row in ih_to_rh_df.iterrows():
        if row['Similarity_Score'] >= 90.0:
            ih_title = str(row['IH_Section_Title'])
            rh_title = str(row['RH_Section_Title'])
            ih_to_rh_lookup[ih_title] = {
                'rh_title': rh_title,
                'similarity': float(row['Similarity_Score'])
            }
    
    print(f"✅ Created {len(ih_to_rh_lookup)} high-confidence IH→RH matches")
    
    print("\nCreating IH→RH traces...")
    ih_rh_traces = []
    
    # Process all IH sections that have RH matches
    traces_created = 0
    target_traces_found = 0
    
    for ih_idx, ih_row in ih_df.iterrows():
        ih_title = str(ih_row.get('Section Title', ''))
        ih_text = str(ih_row.get('Body Text', ''))
        
        # Check if this IH section has an RH match
        if ih_title in ih_to_rh_lookup:
            rh_info = ih_to_rh_lookup[ih_title]
            rh_title = rh_info['rh_title']
            
            # Get RH section data
            rh_section = rh_df[rh_df['Section Title'] == rh_title]
            if not rh_section.empty:
                rh_row = rh_section.iloc[0]
                
                # Create IH→RH trace
                trace = {
                    'trace_id': f"ih_rh_{ih_idx}",
                    'origin': 'IH',
                    'ih_section': {
                        'title': ih_title,
                        'text': ih_text,
                        'stage': 'IH'
                    },
                    'rh_section': {
                        'title': str(rh_row.get('Section Title', '')),
                        'text': str(rh_row.get('Body Text', '')),
                        'stage': 'RH',
                        'similarity_from_ih': rh_info['similarity']
                    }
                }
                
                ih_rh_traces.append(trace)
                traces_created += 1
                
                # Count target sections
                if any(target_num in ih_title for target_num in ['101', '105', '204']):
                    target_traces_found += 1
    
    print(f"\n✅ Created {len(ih_rh_traces)} IH→RH traces")
    print(f"   📊 {traces_created} traces created")
    print(f"   📊 {target_traces_found} target traces found")
    
    return ih_rh_traces

def create_content_focused_website(traces):
    """Create website with content-focused diff that ignores formatting"""
    
    html_content = f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HR5009 Tracing Tool</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }}
        
        .header {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            padding: 2rem 0;
            box-shadow: 0 2px 20px rgba(0,0,0,0.1);
            position: sticky;
            top: 0;
            z-index: 100;
        }}
        
        .header-content {{
            max-width: 1400px;
            margin: 0 auto;
            text-align: center;
            padding: 0 2rem;
        }}
        
        .header h1 {{
            color: #2c3e50;
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
        }}
        
        .stats-bar {{
            display: flex;
            justify-content: center;
            gap: 2rem;
            margin: 1rem 0;
            flex-wrap: wrap;
        }}
        
        .stat-item {{
            background: rgba(52, 152, 219, 0.1);
            border: 2px solid #3498db;
            border-radius: 20px;
            padding: 0.5rem 1rem;
            font-weight: bold;
            color: #2c3e50;
        }}
        
        .controls {{
            max-width: 1400px;
            margin: 1rem auto;
            padding: 0 2rem;
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
            align-items: center;
        }}
        
        .filter-btn {{
            background: #3498db;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            cursor: pointer;
            font-size: 0.9rem;
            transition: all 0.3s ease;
        }}
        
        .filter-btn:hover {{
            background: #2980b9;
            transform: translateY(-2px);
        }}
        
        .filter-btn.active {{
            background: #e74c3c;
        }}
        
        .search-input {{
            padding: 0.5rem 1rem;
            border: none;
            border-radius: 20px;
            font-size: 0.9rem;
            width: 300px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .main-content {{
            max-width: 1400px;
            margin: 2rem auto;
            padding: 0 2rem;
        }}
        
        .traces-container {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 1.5rem;
        }}
        
        .trace-card {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 1.5rem;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            cursor: pointer;
            transition: all 0.3s ease;
            border-left: 5px solid #3498db;
            position: relative;
        }}
        
        .trace-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 12px 40px rgba(0,0,0,0.15);
        }}
        
        .trace-title {{
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 1rem;
            line-height: 1.4;
        }}
        
        .trace-path {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            flex-wrap: wrap;
            margin-bottom: 1rem;
        }}
        
        .stage-indicator {{
            padding: 0.25rem 0.75rem;
            border-radius: 15px;
            font-size: 0.8rem;
            font-weight: bold;
            color: white;
        }}
        
        .stage-ih {{ background: #e74c3c; }}
        .stage-rh {{ background: #f39c12; }}
        
        .trace-arrow {{
            color: #7f8c8d;
            font-weight: bold;
        }}
        
        .trace-preview {{
            color: #7f8c8d;
            font-size: 0.9rem;
            line-height: 1.4;
        }}
        

        
        /* Modal styles */
        .trace-modal {{
            display: none;
            position: fixed;
            z-index: 2000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.9);
            backdrop-filter: blur(5px);
        }}
        
        .trace-modal.active {{
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        
        .modal-content {{
            background: white;
            border-radius: 20px;
            width: 95vw;
            height: 95vh;
            overflow: hidden;
            box-shadow: 0 20px 60px rgba(0,0,0,0.5);
        }}
        
        .modal-header {{
            background: linear-gradient(135deg, #3498db, #2980b9);
            color: white;
            padding: 1.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .modal-close {{
            background: none;
            border: none;
            color: white;
            font-size: 1.5rem;
            cursor: pointer;
            padding: 0.5rem;
            border-radius: 50%;
        }}
        
        .modal-body {{
            height: calc(95vh - 100px);
            overflow-y: auto;
            padding: 1rem;
        }}
        
        .diff-comparison {{
            border: 2px solid #e74c3c;
            border-radius: 15px;
            overflow: hidden;
            margin-top: 1rem;
        }}
        
        .diff-header {{
            background: linear-gradient(135deg, #e74c3c, #c0392b);
            color: white;
            padding: 1rem;
            text-align: center;
        }}
        
        .diff-body {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            min-height: 500px;
        }}
        
        .diff-side {{
            padding: 1.5rem;
            font-family: 'Georgia', 'Times New Roman', serif;
            font-size: 0.95rem;
            line-height: 1.6;
            overflow-y: auto;
            max-height: 500px;
            background: #fafbfc;
        }}
        
        .diff-side:first-child {{
            border-right: 3px solid #e1e4e8;
        }}
        
        .diff-side-header {{
            font-weight: bold;
            color: #24292e;
            margin-bottom: 1.5rem;
            padding-bottom: 0.75rem;
            border-bottom: 2px solid #d1d5da;
            font-family: 'Segoe UI', sans-serif;
            position: sticky;
            top: 0;
            background: #fafbfc;
            z-index: 10;
            font-size: 1.1rem;
        }}
        
        /* Content-focused diff styles */
        .content-added {{
            background-color: #d4edda;
            color: #155724;
            padding: 0.2rem 0.4rem;
            border-radius: 4px;
            font-weight: 500;
            border-left: 3px solid #28a745;
            margin: 0.2rem 0;
            display: inline-block;
        }}
        
        .content-removed {{
            background-color: #f8d7da;
            color: #721c24;
            padding: 0.2rem 0.4rem;
            border-radius: 4px;
            text-decoration: line-through;
            font-weight: 500;
            border-left: 3px solid #dc3545;
            margin: 0.2rem 0;
            display: inline-block;
        }}
        
        .content-unchanged {{
            color: #333;
        }}
        
        .content-modified {{
            background-color: #fff3cd;
            color: #856404;
            padding: 0.2rem 0.4rem;
            border-radius: 4px;
            font-weight: 500;
            border-left: 3px solid #ffc107;
            margin: 0.2rem 0;
            display: inline-block;
        }}
        
        .diff-stats {{
            background: linear-gradient(135deg, #f8f9fa, #e9ecef);
            padding: 1.5rem;
            border-radius: 12px;
            margin-bottom: 1rem;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 1rem;
            text-align: center;
            border: 1px solid #dee2e6;
        }}
        
        .stat-box {{
            padding: 1rem;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        .stat-added {{ 
            background: linear-gradient(135deg, #f0fff4, #dcffe4); 
            color: #22863a; 
            border-left: 4px solid #34d058;
        }}
        .stat-removed {{ 
            background: linear-gradient(135deg, #ffeef0, #fdb8c0); 
            color: #d73a49; 
            border-left: 4px solid #d73a49;
        }}
        .stat-unchanged {{ 
            background: linear-gradient(135deg, #f6f8fa, #e1e4e8); 
            color: #586069; 
            border-left: 4px solid #959da5;
        }}
        .stat-similarity {{ 
            background: linear-gradient(135deg, #e3f2fd, #bbdefb); 
            color: #1976d2; 
            border-left: 4px solid #2196f3;
        }}
        
        .stat-number {{
            font-size: 1.8rem;
            font-weight: bold;
            margin-bottom: 0.25rem;
        }}
        
        .stat-label {{
            font-size: 0.9rem;
            font-weight: 500;
        }}
        
        .diff-note {{
            background: #e3f2fd;
            border: 1px solid #2196f3;
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
            font-size: 0.9rem;
            color: #1565c0;
        }}
    </style>
</head>
<body>
    <!-- Header -->
    <header class="header">
        <div class="header-content">
            <h1><i class="fas fa-shield-alt"></i> HR5009 Tracing Tool</h1>
            <h2>H.R. 8070 IH --> RH</h2>

        </div>
    </header>
    
    <!-- Controls -->
    <div class="controls">
        <button class="filter-btn active" onclick="filterTraces('all')">All Sections</button>
        <input type="text" class="search-input" placeholder="Search sections..." onkeyup="searchTraces(this.value)">
    </div>

    <!-- Main Content -->
    <main class="main-content">
        <div id="traces-container" class="traces-container">
            <!-- Traces will be loaded here -->
        </div>
    </main>

    <!-- Modal -->
    <div id="trace-modal" class="trace-modal">
        <div class="modal-content">
            <div class="modal-header">
                <h3 id="modal-title"><i class="fas fa-shield-alt"></i> Content Analysis</h3>
                <button class="modal-close" onclick="closeModal()"><i class="fas fa-times"></i></button>
            </div>
            <div class="modal-body">
                <div class="diff-note">
                    <strong>Note:</strong> This diff focuses on meaningful content changes and ignores minor spacing, formatting, and punctuation differences.
                </div>
                <div id="diff-stats" class="diff-stats"></div>
                <div id="diff-comparison" class="diff-comparison">
                    <div class="diff-header">
                        <h4 id="diff-title">Content-Focused Comparison</h4>
                    </div>
                    <div class="diff-body">
                        <div class="diff-side">
                            <div class="diff-side-header">IH - Introduced</div>
                            <div id="diff-left-content"></div>
                        </div>
                        <div class="diff-side">
                            <div class="diff-side-header">RH - Committee</div>
                            <div id="diff-right-content"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Global variables
        let tracesData = {json.dumps(traces, indent=2)};
        let currentTrace = null;
        let filteredTraces = tracesData;



        // Initialize
        document.addEventListener('DOMContentLoaded', function() {{
            console.log('Loaded IH→RH traces:', tracesData.length);
            renderTraces();
            setupEventListeners();
        }});

        function setupEventListeners() {{
            document.addEventListener('click', function(e) {{
                if (e.target.classList.contains('trace-modal')) {{
                    closeModal();
                }}
            }});
        }}

        function renderTraces() {{
            const container = document.getElementById('traces-container');
            container.innerHTML = '';

            filteredTraces.forEach((trace, index) => {{
                const card = createTraceCard(trace, index);
                container.appendChild(card);
            }});
        }}

        function createTraceCard(trace, index) {{
            const card = document.createElement('div');
            card.className = 'trace-card';
            card.style.position = 'relative';
            card.onclick = () => openTraceModal(trace);
            
            const displayTitle = trace.ih_section.title;
            
            // Create path indicators (IH → RH only)
            const pathHtml = `
                <span class="stage-indicator stage-ih">IH</span>
                <span class="trace-arrow">→</span>
                <span class="stage-indicator stage-rh">RH</span>
            `;
            
            // Get preview text
            const previewText = trace.ih_section.text;
            const preview = previewText.substring(0, 200) + (previewText.length > 200 ? '...' : '');
            
            card.innerHTML = `
                <div class="trace-title">${{displayTitle}}</div>
                <div class="trace-path">${{pathHtml}}</div>
                <div class="trace-preview">${{preview}}</div>
            `;

            return card;
        }}

        function filterTraces(filter) {{
            // Update active button
            document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            
            switch(filter) {{
                case 'all':
                    filteredTraces = tracesData;
                    break;
            }}
            
            renderTraces();
        }}

        function searchTraces(query) {{
            if (!query.trim()) {{
                filteredTraces = tracesData;
                renderTraces();
                return;
            }}
            
            const lowerQuery = query.toLowerCase();
            filteredTraces = tracesData.filter(trace => {{
                const title = trace.ih_section.title.toLowerCase();
                const text = trace.ih_section.text.toLowerCase();
                return title.includes(lowerQuery) || text.includes(lowerQuery);
            }});
            
            renderTraces();
        }}

        function openTraceModal(trace) {{
            currentTrace = trace;
            
            const displayTitle = trace.ih_section.title;
            document.getElementById('modal-title').innerHTML = 
                `<i class="fas fa-shield-alt"></i> ${{displayTitle}}`;
            
            showContentFocusedDiff();
            
            document.getElementById('trace-modal').classList.add('active');
        }}

        function showContentFocusedDiff() {{
            const trace = currentTrace;
            const leftText = trace.ih_section.text;
            const rightText = trace.rh_section.text;
            
            generateContentFocusedDiff(leftText, rightText);
        }}

        function normalizeText(text) {{
            // Normalize text for content comparison
            return text
                // Normalize whitespace
                .replace(/\\s+/g, ' ')
                // Normalize punctuation
                .replace(/\\s*([.,:;])\\s*/g, '$1 ')
                // Normalize parentheses and brackets
                .replace(/\\s*([\\(\\)\\[\\]])\\s*/g, '$1')
                // Remove extra spaces around dashes
                .replace(/\\s*[-—–]\\s*/g, '—')
                // Normalize quotes
                .replace(/["'"']/g, '"')
                // Remove multiple spaces
                .replace(/\\s+/g, ' ')
                .trim();
        }}

        function generateContentFocusedDiff(text1, text2) {{
            const leftContainer = document.getElementById('diff-left-content');
            const rightContainer = document.getElementById('diff-right-content');
            const statsContainer = document.getElementById('diff-stats');
            
            // Normalize texts for better comparison
            const normalizedText1 = normalizeText(text1);
            const normalizedText2 = normalizeText(text2);
            
            // Split into semantic chunks (sentences or clauses)
            const chunks1 = splitIntoSemanticChunks(normalizedText1);
            const chunks2 = splitIntoSemanticChunks(normalizedText2);
            
            // Use content-focused diff algorithm
            const diffResult = computeContentDiff(chunks1, chunks2);
            
            leftContainer.innerHTML = diffResult.leftHtml;
            rightContainer.innerHTML = diffResult.rightHtml;
            
            // Calculate stats
            const totalChunks = Math.max(chunks1.length, chunks2.length);
            const similarity = totalChunks > 0 ? Math.round((diffResult.stats.unchanged / totalChunks) * 100) : 100;
            
            // Update stats
            statsContainer.innerHTML = `
                <div class="stat-box stat-added">
                    <div class="stat-number">${{diffResult.stats.added}}</div>
                    <div class="stat-label">Added Content</div>
                </div>
                <div class="stat-box stat-removed">
                    <div class="stat-number">${{diffResult.stats.removed}}</div>
                    <div class="stat-label">Removed Content</div>
                </div>
                <div class="stat-box stat-unchanged">
                    <div class="stat-number">${{diffResult.stats.unchanged}}</div>
                    <div class="stat-label">Unchanged Content</div>
                </div>
                <div class="stat-box stat-similarity">
                    <div class="stat-number">${{similarity}}%</div>
                    <div class="stat-label">Content Similarity</div>
                </div>
            `;
        }}

        function splitIntoSemanticChunks(text) {{
            // Split text into meaningful chunks (clauses, phrases)
            return text
                .split(/[.;:]/)
                .map(chunk => chunk.trim())
                .filter(chunk => chunk.length > 0);
        }}

        function computeContentDiff(chunks1, chunks2) {{
            let leftHtml = '';
            let rightHtml = '';
            let stats = {{ added: 0, removed: 0, unchanged: 0 }};
            
            // Use a similarity-based matching approach
            const used2 = new Set();
            
            for (let i = 0; i < chunks1.length; i++) {{
                const chunk1 = chunks1[i];
                let bestMatch = -1;
                let bestSimilarity = 0;
                
                // Find best matching chunk in text2
                for (let j = 0; j < chunks2.length; j++) {{
                    if (used2.has(j)) continue;
                    
                    const chunk2 = chunks2[j];
                    const similarity = calculateContentSimilarity(chunk1, chunk2);
                    
                    if (similarity > bestSimilarity && similarity > 0.7) {{
                        bestSimilarity = similarity;
                        bestMatch = j;
                    }}
                }}
                
                if (bestMatch !== -1) {{
                    // Found a good match
                    used2.add(bestMatch);
                    const chunk2 = chunks2[bestMatch];
                    
                    if (bestSimilarity > 0.95) {{
                        // Very similar - show as unchanged
                        leftHtml += `<span class="content-unchanged">${{escapeHtml(chunk1)}}.</span> `;
                        rightHtml += `<span class="content-unchanged">${{escapeHtml(chunk2)}}.</span> `;
                        stats.unchanged++;
                    }} else {{
                        // Similar but modified
                        leftHtml += `<span class="content-modified">${{escapeHtml(chunk1)}}.</span> `;
                        rightHtml += `<span class="content-modified">${{escapeHtml(chunk2)}}.</span> `;
                        stats.unchanged++;
                    }}
                }} else {{
                    // No match found - removed
                    leftHtml += `<span class="content-removed">${{escapeHtml(chunk1)}}.</span> `;
                    stats.removed++;
                }}
            }}
            
            // Add unmatched chunks from text2 as added
            for (let j = 0; j < chunks2.length; j++) {{
                if (!used2.has(j)) {{
                    rightHtml += `<span class="content-added">${{escapeHtml(chunks2[j])}}.</span> `;
                    stats.added++;
                }}
            }}
            
            return {{
                leftHtml: leftHtml,
                rightHtml: rightHtml,
                stats: stats
            }};
        }}

        function calculateContentSimilarity(text1, text2) {{
            // Simple content similarity based on common words
            const words1 = text1.toLowerCase().split(/\\s+/);
            const words2 = text2.toLowerCase().split(/\\s+/);
            
            const set1 = new Set(words1);
            const set2 = new Set(words2);
            
            const intersection = new Set([...set1].filter(x => set2.has(x)));
            const union = new Set([...set1, ...set2]);
            
            return intersection.size / union.size;
        }}

        function escapeHtml(text) {{
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }}

        function closeModal() {{
            document.getElementById('trace-modal').classList.remove('active');
        }}
    </script>
</body>
</html>
    '''
    
    with open('content_focused_diff_website.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("✅ Created content-focused diff website: content_focused_diff_website.html")

def start_content_focused_server():
    """Start server for content-focused diff website"""
    port = 8016
    try:
        with socketserver.TCPServer(("", port), http.server.SimpleHTTPRequestHandler) as httpd:
            url = f"http://localhost:{port}/content_focused_diff_website.html"
            
            print(f"🚀 Content-focused server running at: {url}")
            
            # Open browser
            def open_browser():
                time.sleep(1)
                webbrowser.open(url)
            
            threading.Thread(target=open_browser, daemon=True).start()
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")

def main():
    """Main function"""
    print("=" * 80)
    print("CONTENT-FOCUSED DIFF WEBSITE")
    print("Focuses on meaningful content changes, ignores formatting")
    print("=" * 80)
    
    # Load IH→RH traces
    traces = load_ih_to_rh_traces()
    
    print("\nCreating content-focused website...")
    create_content_focused_website(traces)
    
    print("\n🎉 Content-focused website ready!")
    print("📁 File created: content_focused_diff_website.html")
    
    print("\n🔧 Content-Focused Features:")
    print("   ✅ Ignores spacing and formatting differences")
    print("   ✅ Focuses on meaningful content changes")
    print("   ✅ Normalizes punctuation and whitespace")
    print("   ✅ Semantic chunk-based comparison")
    print("   ✅ Similarity-based matching (not position-based)")
    print("   ✅ Clear visual indicators for content changes")
    
    # Start server
    print("\n🌐 Starting content-focused web server...")
    start_content_focused_server()

if __name__ == "__main__":
    main() 