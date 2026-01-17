#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTML to PDF converter with Chinese font support
"""

import os
import sys
from pathlib import Path

# Install required package
try:
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from xhtml2pdf import pisa
except ImportError:
    import subprocess
    print("Installing required packages...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "xhtml2pdf", "reportlab", "-q"])
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from xhtml2pdf import pisa

def register_chinese_fonts():
    """Register Chinese fonts from Windows system"""
    import platform

    if platform.system() == 'Windows':
        # Common Windows font paths
        font_paths = [
            'C:/Windows/Fonts/simhei.ttf',  # SimHei (黑体)
            'C:/Windows/Fonts/simsun.ttc',  # SimSun (宋体)
            'C:/Windows/Fonts/msyh.ttc',    # Microsoft YaHei (微软雅黑)
        ]

        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    font_name = os.path.splitext(os.path.basename(font_path))[0]
                    pdfmetrics.registerFont(TTFont(font_name, font_path))
                    print(f"[OK] Registered font: {font_name}")
                    return font_name
                except Exception as e:
                    print(f"[WARN] Failed to register {font_path}: {e}")
                    continue

    return None

def create_simple_pdf(md_file, pdf_file):
    """Create PDF with simple HTML and Chinese font support"""
    print(f"Converting {md_file} to PDF with Chinese font support...")

    # Register Chinese fonts
    font_name = register_chinese_fonts()

    # Read Markdown file
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Convert Markdown to simple HTML (without using markdown library for better compatibility)
    # Just wrap content in basic HTML with minimal styling
    html_content = f"""<!DOCTYPE html>
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
            line-height: 1.8;
            font-size: 11pt;
        }}
        h1 {{
            color: #1a237e;
            font-size: 20pt;
            margin-top: 20pt;
            margin-bottom: 10pt;
            page-break-after: avoid;
        }}
        h2 {{
            color: #283593;
            font-size: 16pt;
            margin-top: 15pt;
            margin-bottom: 8pt;
            page-break-after: avoid;
        }}
        h3 {{
            color: #3949ab;
            font-size: 13pt;
            margin-top: 12pt;
            margin-bottom: 6pt;
            page-break-after: avoid;
        }}
        p {{
            margin: 8pt 0;
            text-align: justify;
        }}
        code {{
            background-color: #f4f4f4;
            padding: 2pt 4pt;
            font-family: Consolas, monospace;
            font-size: 9pt;
        }}
        pre {{
            background-color: #f4f4f4;
            padding: 8pt;
            border-left: 3pt solid #999;
            page-break-inside: avoid;
            font-size: 9pt;
        }}
        strong {{
            color: #d32f2f;
            font-weight: bold;
        }}
        img {{
            max-width: 100%;
            height: auto;
            display: block;
            margin: 10pt auto;
        }}
        hr {{
            border: none;
            border-top: 1pt solid #ddd;
            margin: 15pt 0;
        }}
    </style>
</head>
<body>
"""

    # Simple Markdown parsing (basic support)
    lines = content.split('\n')
    in_code_block = False

    for line in lines:
        # Code blocks
        if line.strip().startswith('```'):
            if in_code_block:
                html_content += '</pre>\n'
                in_code_block = False
            else:
                html_content += '<pre><code>'
                in_code_block = True
            continue

        if in_code_block:
            html_content += line + '\n'
            continue

        # Headers
        if line.startswith('# '):
            html_content += f'<h1>{line[2:]}</h1>\n'
        elif line.startswith('## '):
            html_content += f'<h2>{line[3:]}</h2>\n'
        elif line.startswith('### '):
            html_content += f'<h3>{line[4:]}</h3>\n'
        # Horizontal rule
        elif line.strip() == '---':
            html_content += '<hr/>\n'
        # Images
        elif line.strip().startswith('!['):
            # Extract image markdown: ![alt](url)
            import re
            match = re.match(r'!\[(.*?)\]\((.*?)\)', line.strip())
            if match:
                alt, url = match.groups()
                # Convert relative path to absolute
                img_path = os.path.join(os.path.dirname(md_file), url)
                html_content += f'<img src="{img_path}" alt="{alt}"/>\n'
            html_content += f'<p style="text-align:center;font-size:9pt;color:#666;"><em>{line.strip()[line.strip().find("*"):].strip("*")}</em></p>\n'
        # Bold text
        elif '**' in line:
            line = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', line)
            html_content += f'<p>{line}</p>\n'
        # Inline code
        elif '`' in line:
            line = re.sub(r'`(.*?)`', r'<code>\1</code>', line)
            html_content += f'<p>{line}</p>\n'
        # Empty line
        elif line.strip() == '':
            html_content += '<br/>\n'
        # Regular paragraph
        else:
            html_content += f'<p>{line}</p>\n'

    html_content += """
</body>
</html>
"""

    # Write HTML temporarily for debugging
    temp_html = pdf_file.replace('.pdf', '_temp.html')
    with open(temp_html, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"[DEBUG] Temporary HTML saved: {temp_html}")

    # Convert to PDF
    try:
        with open(pdf_file, 'wb') as pdf:
            pisa_status = pisa.CreatePDF(
                html_content,
                dest=pdf,
                encoding='utf-8'
            )

        if pisa_status.err:
            print(f"[WARN] PDF created with warnings")
        else:
            print(f"[OK] PDF created: {pdf_file}")

        # Clean up temp HTML
        if os.path.exists(temp_html):
            os.remove(temp_html)

        return pdf_file
    except Exception as e:
        print(f"[ERROR] Failed to create PDF: {e}")
        print("\n[Alternative] Please try using wkhtmltopdf or browser Print-to-PDF")
        return None

def main():
    base_dir = Path(__file__).parent
    md_file = base_dir / "paper-explanation-20260114-134500.md"
    pdf_file = base_dir / "paper-explanation-20260114-134500-fixed.pdf"

    if not md_file.exists():
        print(f"Error: Markdown file not found: {md_file}")
        sys.exit(1)

    print("="*70)
    print("PDF Generator with Chinese Font Support")
    print("="*70)

    result = create_simple_pdf(str(md_file), str(pdf_file))

    if result and os.path.exists(pdf_file):
        size_mb = os.path.getsize(pdf_file) / (1024 * 1024)
        print(f"\n[SUCCESS] PDF file: {pdf_file.name} ({size_mb:.1f} MB)")
        print("\nIf Chinese characters still don't display correctly,")
        print("please use your browser to open the HTML file and print to PDF.")
    else:
        print("\n[FAILED] Could not generate PDF with Chinese support")

    print("="*70)

if __name__ == "__main__":
    main()
