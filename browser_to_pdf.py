#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用浏览器自动生成PDF（确保中文正确显示）
"""

import os
import sys
import subprocess
from pathlib import Path

def generate_pdf_via_browser(html_file, pdf_file):
    """使用浏览器的打印功能生成PDF"""
    print(f"Generating PDF from {html_file}...")

    # 方法1: 尝试使用Microsoft Edge (Windows自带)
    edge_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]

    for edge_path in edge_paths:
        if os.path.exists(edge_path):
            print(f"[INFO] Found Microsoft Edge: {edge_path}")
            try:
                # 使用Edge的headless模式打印为PDF
                cmd = [
                    edge_path,
                    "--headless",
                    "--disable-gpu",
                    f"--print-to-pdf={pdf_file}",
                    f"file:///{html_file.replace(os.sep, '/')}"
                ]
                print(f"[INFO] Running: {' '.join(cmd[:3])} ...")
                result = subprocess.run(cmd, capture_output=True, timeout=30)

                if os.path.exists(pdf_file):
                    size_mb = os.path.getsize(pdf_file) / (1024 * 1024)
                    print(f"[OK] PDF generated successfully: {pdf_file} ({size_mb:.1f} MB)")
                    return True
                else:
                    print(f"[WARN] Edge command completed but PDF not found")
            except Exception as e:
                print(f"[ERROR] Edge failed: {e}")

    # 方法2: 尝试使用Chrome
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]

    for chrome_path in chrome_paths:
        if os.path.exists(chrome_path):
            print(f"[INFO] Found Google Chrome: {chrome_path}")
            try:
                cmd = [
                    chrome_path,
                    "--headless",
                    "--disable-gpu",
                    f"--print-to-pdf={pdf_file}",
                    f"file:///{html_file.replace(os.sep, '/')}"
                ]
                print(f"[INFO] Running: {' '.join(cmd[:3])} ...")
                result = subprocess.run(cmd, capture_output=True, timeout=30)

                if os.path.exists(pdf_file):
                    size_mb = os.path.getsize(pdf_file) / (1024 * 1024)
                    print(f"[OK] PDF generated successfully: {pdf_file} ({size_mb:.1f} MB)")
                    return True
            except Exception as e:
                print(f"[ERROR] Chrome failed: {e}")

    print("\n[FAILED] No suitable browser found for automatic PDF generation")
    return False

def show_manual_instructions(html_file):
    """显示手动生成PDF的说明"""
    print("\n" + "="*70)
    print("Manual PDF Generation Instructions")
    print("="*70)
    print(f"\n1. Open this file in your browser:")
    print(f"   {html_file}")
    print(f"\n2. Press Ctrl+P (or Cmd+P on Mac)")
    print(f"\n3. Select 'Save as PDF' as the destination")
    print(f"\n4. Click 'Save' and choose your location")
    print(f"\n5. The PDF will have perfect Chinese font rendering!")
    print("\n" + "="*70)

def main():
    base_dir = Path(__file__).parent
    html_file = base_dir / "paper-explanation-20260114-134500.html"
    pdf_file = base_dir / "paper-explanation-20260114-134500-browser.pdf"

    if not html_file.exists():
        print(f"Error: HTML file not found: {html_file}")
        sys.exit(1)

    print("="*70)
    print("Browser-based PDF Generator (Perfect Chinese Support)")
    print("="*70)
    print()

    # 尝试自动生成
    success = generate_pdf_via_browser(str(html_file), str(pdf_file))

    if not success:
        # 如果自动生成失败，显示手动说明
        show_manual_instructions(str(html_file.absolute()))

        # 尝试在浏览器中打开HTML
        try:
            print("\n[INFO] Opening HTML file in default browser...")
            if sys.platform == 'win32':
                os.startfile(str(html_file))
            elif sys.platform == 'darwin':
                subprocess.call(['open', str(html_file)])
            else:
                subprocess.call(['xdg-open', str(html_file)])
            print("[OK] HTML file opened in browser")
        except Exception as e:
            print(f"[ERROR] Could not open browser: {e}")

    print("\n" + "="*70)

if __name__ == "__main__":
    main()
