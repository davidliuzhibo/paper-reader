#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTML to PDF converter (simplified for better compatibility)
"""

import os
import sys
from pathlib import Path

# Install required package
try:
    from xhtml2pdf import pisa
except ImportError:
    import subprocess
    print("Installing xhtml2pdf...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "xhtml2pdf", "-q"])
    from xhtml2pdf import pisa

def convert_html_to_pdf(html_file, pdf_file):
    """Convert HTML to PDF with simplified CSS"""
    print(f"Converting {html_file} to PDF...")

    # Read HTML
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Create simplified HTML for PDF
    simplified_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        @page {{
            size: A4;
            margin: 2cm;
        }}
        body {{
            font-family: SimSun, serif;
            line-height: 1.6;
            color: #333;
        }}
        h1 {{
            color: #1a237e;
            border-bottom: 2px solid #3f51b5;
            padding-bottom: 8px;
            page-break-after: avoid;
        }}
        h2 {{
            color: #283593;
            border-left: 3px solid #3f51b5;
            padding-left: 10px;
            page-break-after: avoid;
        }}
        h3 {{
            color: #3949ab;
            page-break-after: avoid;
        }}
        p {{
            text-align: justify;
            margin: 10px 0;
        }}
        code {{
            background-color: #f4f4f4;
            padding: 2px 4px;
            font-family: Consolas, monospace;
        }}
        pre {{
            background-color: #f4f4f4;
            padding: 10px;
            border-left: 3px solid #999;
            page-break-inside: avoid;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 15px 0;
            page-break-inside: avoid;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        th {{
            background-color: #3f51b5;
            color: white;
        }}
        strong {{
            color: #d32f2f;
        }}
        hr {{
            border: none;
            border-top: 1px solid #ddd;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
"""

    # Extract content from HTML (remove container div and complex styles)
    import re
    # Find content between <div class="container"> and </div>
    match = re.search(r'<div class="container">(.*?)</div>\s*</body>', html_content, re.DOTALL)
    if match:
        content = match.group(1)
    else:
        # Fallback: extract body content
        match = re.search(r'<body>(.*?)</body>', html_content, re.DOTALL)
        content = match.group(1) if match else html_content

    simplified_html += content
    simplified_html += """
</body>
</html>
"""

    # Convert to PDF
    try:
        with open(pdf_file, 'wb') as pdf:
            pisa_status = pisa.CreatePDF(
                simplified_html,
                dest=pdf,
                encoding='utf-8'
            )

        if pisa_status.err:
            print(f"[WARN] PDF created with some warnings")
        else:
            print(f"[OK] PDF created successfully: {pdf_file}")

        return pdf_file
    except Exception as e:
        print(f"[ERROR] Failed to create PDF: {e}")
        return None

def main():
    base_dir = Path(__file__).parent
    html_file = base_dir / "paper-explanation-20260114-134500.html"
    pdf_file = base_dir / "paper-explanation-20260114-134500.pdf"

    if not html_file.exists():
        print(f"Error: HTML file not found: {html_file}")
        sys.exit(1)

    print("="*60)
    print("HTML to PDF Converter")
    print("="*60)

    result = convert_html_to_pdf(str(html_file), str(pdf_file))

    if result and os.path.exists(pdf_file):
        size_kb = os.path.getsize(pdf_file) // 1024
        print(f"\n[SUCCESS] PDF file: {pdf_file.name} ({size_kb} KB)")
    else:
        print("\n[FAILED] Could not generate PDF")
        print("Alternative: Open HTML in browser and use Print > Save as PDF")

    print("="*60)

if __name__ == "__main__":
    main()
