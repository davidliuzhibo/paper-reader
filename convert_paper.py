#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
论文解读文档转换工具 (简化版)
将Markdown转换为HTML和PDF格式
"""

import os
import sys
from pathlib import Path

def install_packages():
    """安装必要的包"""
    import subprocess
    packages = {
        'markdown': 'markdown',
        'xhtml2pdf': 'xhtml2pdf'
    }
    for module_name, package_name in packages.items():
        try:
            __import__(module_name)
        except ImportError:
            print(f"正在安装 {package_name}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package_name, "-q"])

# 安装必要的包
install_packages()

import markdown
from xhtml2pdf import pisa

def convert_md_to_html(md_file, html_file):
    """将Markdown转换为HTML"""
    print(f"正在转换 {md_file} 到 HTML...")

    # 读取Markdown文件
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # 配置Markdown扩展
    extensions = [
        'markdown.extensions.extra',
        'markdown.extensions.codehilite',
        'markdown.extensions.toc',
        'markdown.extensions.tables',
        'markdown.extensions.fenced_code'
    ]

    # 转换为HTML
    html_content = markdown.markdown(md_content, extensions=extensions)

    # 添加HTML模板和样式
    html_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Attention Is All You Need - 论文解读</title>
    <style>
        body {{
            font-family: "Microsoft YaHei", "微软雅黑", "SimSun", "宋体", sans-serif;
            line-height: 1.8;
            max-width: 900px;
            margin: 0 auto;
            padding: 40px 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
        }}
        .container {{
            background-color: white;
            padding: 50px;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #1a237e;
            border-bottom: 3px solid #3f51b5;
            padding-bottom: 10px;
            margin-top: 40px;
            font-size: 2.2em;
        }}
        h2 {{
            color: #283593;
            border-left: 4px solid #3f51b5;
            padding-left: 15px;
            margin-top: 35px;
            font-size: 1.8em;
        }}
        h3 {{
            color: #3949ab;
            margin-top: 25px;
            font-size: 1.4em;
        }}
        p {{
            text-align: justify;
            margin: 15px 0;
            font-size: 1.05em;
        }}
        code {{
            background-color: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: "Consolas", "Monaco", "Courier New", monospace;
            font-size: 0.9em;
            color: #e91e63;
        }}
        pre {{
            background-color: #2b2b2b;
            color: #f8f8f2;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
            font-family: "Consolas", "Monaco", "Courier New", monospace;
        }}
        pre code {{
            background-color: transparent;
            color: inherit;
            padding: 0;
        }}
        blockquote {{
            border-left: 4px solid #ffb74d;
            padding-left: 15px;
            margin: 20px 0;
            color: #666;
            font-style: italic;
            background-color: #fff8e1;
            padding: 15px;
            border-radius: 5px;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
            background-color: white;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #3f51b5;
            color: white;
            font-weight: bold;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        ul, ol {{
            margin: 15px 0;
            padding-left: 30px;
        }}
        li {{
            margin: 8px 0;
        }}
        strong {{
            color: #d32f2f;
            font-weight: 600;
        }}
        hr {{
            border: none;
            border-top: 2px solid #e0e0e0;
            margin: 30px 0;
        }}
        .metadata {{
            background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            border-left: 4px solid #2196f3;
        }}
        footer {{
            margin-top: 60px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            text-align: center;
            color: #999;
            font-size: 0.9em;
        }}
        @media print {{
            body {{
                background: white;
            }}
            .container {{
                box-shadow: none;
                padding: 20px;
            }}
        }}
    </style>
</head>
<body>
<div class="container">
{html_content}
<footer>
    <p>📚 本解读由 Claude Code (lunwen skill) 自动生成</p>
    <p>🕐 生成时间: 2026年1月14日 | 🤖 基于 Transformer 论文 (Vaswani et al., 2017)</p>
</footer>
</div>
</body>
</html>"""

    # 写入HTML文件
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_template)

    print(f"[OK] HTML file generated: {html_file}")
    return html_file

def convert_html_to_pdf_simple(html_file, pdf_file):
    """将HTML转换为PDF（使用xhtml2pdf）"""
    print(f"正在转换 HTML 到 PDF...")

    try:
        # 读取HTML内容
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()

        # 为PDF优化HTML样式（移除渐变背景等）
        pdf_html = html_content.replace(
            'background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);',
            'background: white;'
        ).replace(
            'background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);',
            'background-color: #e3f2fd;'
        )

        # 转换为PDF
        with open(pdf_file, 'wb') as pdf:
            pisa_status = pisa.CreatePDF(
                pdf_html,
                dest=pdf,
                encoding='utf-8'
            )

        if pisa_status.err:
            print(f"[WARN] PDF generated with warnings: {pdf_file}")
        else:
            print(f"[OK] PDF file generated: {pdf_file}")
        return pdf_file

    except Exception as e:
        print(f"[ERROR] PDF generation failed: {e}")
        print("Tip: Open HTML file in browser and use Print > Save as PDF")
        return None

def main():
    # 设置文件路径
    base_dir = Path(__file__).parent
    md_file = base_dir / "paper-explanation-20260114-134500.md"
    html_file = base_dir / "paper-explanation-20260114-134500.html"
    pdf_file = base_dir / "paper-explanation-20260114-134500.pdf"

    if not md_file.exists():
        print(f"错误: 找不到Markdown文件: {md_file}")
        sys.exit(1)

    print("="*70)
    print("           论文解读文档转换工具 - Transformer Paper")
    print("="*70)
    print()

    # 转换为HTML
    html_result = convert_md_to_html(str(md_file), str(html_file))

    # 转换为PDF
    pdf_result = convert_html_to_pdf_simple(str(html_file), str(pdf_file))

    print()
    print("="*70)
    print("                    Conversion Complete!")
    print("="*70)
    print(f"[MD]  Markdown file: {md_file.name}")
    print(f"[HTML] HTML file:    {html_file.name} ({os.path.getsize(html_file) // 1024} KB)")
    if pdf_result and os.path.exists(pdf_file):
        print(f"[PDF]  PDF file:     {pdf_file.name} ({os.path.getsize(pdf_file) // 1024} KB)")
    print("="*70)
    print()
    print("Tip: Open HTML file in browser for best reading experience!")
    print()

if __name__ == "__main__":
    main()
