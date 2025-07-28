# HR5009 Tracing Tool

A web-based tool for tracing and comparing legislative content changes between H.R. 8070 bill versions (IH → RH stages).

## Features

- **Content-Focused Diff**: Ignores formatting differences and focuses on meaningful content changes
- **Section Comparison**: Displays side-by-side comparisons of legislative sections
- **Semantic Matching**: Uses similarity-based matching for accurate section alignment
- **Clean Interface**: Simple, user-friendly design with search functionality
- **Real-time Diff**: Interactive word-level and chunk-based difference highlighting

## Files

- `content_focused_diff_website.py` - Main Python script that generates the website
- `content_focused_diff_website.html` - Generated HTML interface
- `HR8070-ih-sections.xlsx` - IH (Introduced in House) sections data
- `HR8070-rh-sections.xlsx` - RH (Reported in House) sections data  
- `HR8070_Section_Title_Matches.xlsx` - Section title matching data

## Usage

1. **Install Dependencies**:
   ```bash
   pip install pandas openpyxl
   ```

2. **Run the Tool**:
   ```bash
   python3 content_focused_diff_website.py
   ```

3. **Access the Website**:
   Open your browser and go to: `http://localhost:8016/content_focused_diff_website.html`

## How It Works

1. **Data Loading**: Loads IH and RH section data from Excel files
2. **Matching**: Creates high-confidence matches (≥90% similarity) between sections
3. **Trace Generation**: Builds IH→RH traces for all matched sections
4. **Diff Analysis**: Performs content-focused comparison ignoring formatting
5. **Web Interface**: Generates interactive HTML with search and filtering

## Interface

- **Title**: HR5009 Tracing Tool
- **Subtitle**: H.R. 8070 IH --> RH
- **Controls**: 
  - "All Sections" filter
  - Search box for finding specific sections
- **Section Cards**: Click to view detailed side-by-side comparisons
- **Diff View**: Highlights changes with proper semantic alignment

## Technical Details

- Built with Python 3
- Uses pandas for data processing
- Implements LCS (Longest Common Subsequence) algorithm for text alignment
- Normalizes content for better comparison accuracy
- Serves content via built-in HTTP server

## License

This tool is designed for legislative analysis and transparency. 