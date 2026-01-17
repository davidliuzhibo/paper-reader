#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用Chrome/Edge Headless生成PDF（优化版）
"""

import os
import subprocess
import sys
from pathlib import Path
import time

def generate_pdf_with_longer_timeout(html_file, pdf_file):
    """使用浏览器生成PDF，增加超时时间"""
    print(f"Generating PDF from HTML...")
    print(f"Source: {html_file}")
    print(f"Target: {pdf_file}")

    # 尝试Edge
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    if os.path.exists(edge_path):
        print(f"\n[INFO] Using Microsoft Edge")
        try:
            cmd = [
                edge_path,
                "--headless",
                "--disable-gpu",
                "--no-sandbox",
                "--disable-software-rasterizer",
                f"--print-to-pdf={pdf_file}",
                "--print-to-pdf-no-header",
                f"file:///{html_file.replace(os.sep, '/')}"
            ]

            print(f"[INFO] Starting PDF generation (this may take 1-2 minutes)...")
            print(f"[INFO] Loading images and rendering content...")

            # 增加到120秒超时
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=120,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )

            # 等待文件写入完成
            time.sleep(2)

            if os.path.exists(pdf_file):
                size_mb = os.path.getsize(pdf_file) / (1024 * 1024)
                print(f"\n[SUCCESS] PDF generated: {pdf_file}")
                print(f"[SUCCESS] File size: {size_mb:.1f} MB")
                print(f"\n[INFO] Chinese characters should display correctly!")
                return True
            else:
                print(f"[WARN] Command completed but PDF file not found")
                return False

        except subprocess.TimeoutExpired:
            print(f"[ERROR] Timeout after 120 seconds")
            print(f"[INFO] The HTML file may be too large or complex")
            return False
        except Exception as e:
            print(f"[ERROR] Failed: {e}")
            return False

    # 尝试Chrome
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    if os.path.exists(chrome_path):
        print(f"\n[INFO] Using Google Chrome")
        try:
            cmd = [
                chrome_path,
                "--headless",
                "--disable-gpu",
                "--no-sandbox",
                f"--print-to-pdf={pdf_file}",
                f"file:///{html_file.replace(os.sep, '/')}"
            ]

            print(f"[INFO] Starting PDF generation (this may take 1-2 minutes)...")
            result = subprocess.run(cmd, capture_output=True, timeout=120)

            time.sleep(2)

            if os.path.exists(pdf_file):
                size_mb = os.path.getsize(pdf_file) / (1024 * 1024)
                print(f"\n[SUCCESS] PDF generated: {pdf_file}")
                print(f"[SUCCESS] File size: {size_mb:.1f} MB")
                return True

        except Exception as e:
            print(f"[ERROR] Failed: {e}")
            return False

    return False

def main():
    base_dir = Path(__file__).parent
    html_file = base_dir / "paper-explanation-20260114-134500.html"
    pdf_file = base_dir / "paper-explanation-20260114-134500-fixed.pdf"

    if not html_file.exists():
        print(f"Error: HTML file not found")
        sys.exit(1)

    print("="*70)
    print("PDF Generator with Chinese Font Support (Extended Timeout)")
    print("="*70)
    print()

    success = generate_pdf_with_longer_timeout(
        str(html_file.absolute()),
        str(pdf_file.absolute())
    )

    if not success:
        print("\n" + "="*70)
        print("Alternative: Manual PDF Generation")
        print("="*70)
        print(f"\nThe automatic generation failed.")
        print(f"\nPlease follow these steps for perfect Chinese rendering:")
        print(f"\n1. The HTML file should now be open in your browser")
        print(f"   If not, double-click: {html_file.name}")
        print(f"\n2. Press Ctrl+P (Windows) or Cmd+P (Mac)")
        print(f"\n3. In the print dialog:")
        print(f"   - Destination: Save as PDF")
        print(f"   - Layout: Portrait")
        print(f"   - Margins: Default")
        print(f"   - Background graphics: On")
        print(f"\n4. Click 'Save' button")
        print(f"\n5. Choose your preferred location and filename")
        print(f"\nThis method ensures 100% correct Chinese font display!")
        print("="*70)

        # 打开HTML文件
        try:
            if sys.platform == 'win32':
                os.startfile(str(html_file))
                print(f"\n[OK] HTML file opened in default browser")
        except:
            pass

    print()

if __name__ == "__main__":
    main()
