#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
云端论文解读执行脚本
使用 Claude Agent SDK 调用 Claude 模型（通过 yunwu.ai 代理）
使用阿里通义万相生成配图
输出 Markdown、HTML、PDF 三种格式

环境变量（GitHub Secrets 配置）:
  - ANTHROPIC_API_KEY: yunwu.ai API 密钥
  - ANTHROPIC_BASE_URL: yunwu.ai API 端点
  - ANTHROPIC_MODEL: Claude 模型名称
  - DASHSCOPE_API_KEY: 阿里通义万相 API 密钥
  - DASHSCOPE_BASE_URL: 阿里通义万相 API 端点
  - DASHSCOPE_MODEL: 阿里通义万相模型名称
  - PAPER_PATH: 论文文件路径
"""

import os
import sys
import json
import base64
from datetime import datetime
from pathlib import Path

import anyio
import httpx


# ============================================================
# 配置（从环境变量读取）
# ============================================================
# Claude API 配置（通过 yunwu.ai 代理，由 Agent SDK 自动读取）
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-opus-4-5-20251101")

# Gemini 图像生成配置（通过 yunwu.ai 代理）
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_BASE_URL = os.environ.get("GEMINI_BASE_URL", "https://yunwu.ai/v1beta/models")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3-pro-image-preview")

# 阿里通义万相配置（备用）
DASHSCOPE_API_KEY = os.environ.get("DASHSCOPE_API_KEY")
DASHSCOPE_BASE_URL = os.environ.get("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
DASHSCOPE_MODEL = os.environ.get("DASHSCOPE_MODEL", "wanx2.1-t2i-turbo")

# 论文路径
PAPER_PATH = os.environ.get("PAPER_PATH", "")

# 输出目录
OUTPUT_DIR = Path("outputs")


# ============================================================
# 系统提示词（基于 SKILL.md）
# ============================================================
SYSTEM_PROMPT = """你是一个专门用于阅读学术论文并生成易懂解释的助手。

## 核心原则
采用"黄叔风格"的叙事方式，将复杂的学术内容转化为亲切、易懂的中文解释。

## 风格特征
1. **个人化叙事**: 用第一人称视角，分享真实感受
2. **故事化结构**: 用场景或问题引入，把研究过程讲成探索故事
3. **通俗化表达**: 技术术语必须解释，用类比和比喻，短句为主
4. **真实与反思**: 诚实指出论文局限，分享个人思考
5. **长文深度**: 目标3000-5000字，不怕展开，把概念讲透

## 输出结构
```markdown
# [论文标题的中文翻译]

**原文**: [English Title]
**作者**: [Authors]
**我的解读时间**: [时间]

---

## 开场: 为什么要读这篇论文
[用场景、问题或个人经历引入，100-200字]

## 研究背景: 他们想解决什么问题
[用通俗语言解释研究动机，300-500字]

## 他们是怎么做的: 方法论解读
[把研究方法讲成故事，400-600字]

## 核心发现: 他们发现了什么
[列出3-5个关键发现，每个150-200字]

## 深入思考: 这意味着什么
[分析研究意义，300-400字]

## 局限与展望
[诚实指出不足，200-300字]

## 我的感想
[个人反思，200-300字]

## 总结
[一段话概括，100-150字]

---

**元数据**
📄 论文类型: [类型]
⏱️ 处理时长: [X秒]
🖼️ 配图生成: [状态]
```

## 禁止行为
- 不要输出英文内容（除了原文标题）
- 不要使用学术腔调和术语堆砌
- 不要生成过短的解读（<2000字）

请用中文输出完整的论文解读。
"""


# ============================================================
# 图片生成函数（阿里通义万相 - 使用 DashScope 原生 API）
# ============================================================
async def generate_image_dashscope(prompt: str, image_index: int) -> str | None:
    """调用阿里通义万相 API 生成图片（DashScope 原生格式）"""
    if not DASHSCOPE_API_KEY:
        print(f"[WARN] DASHSCOPE_API_KEY not set, skipping image {image_index}")
        return None

    # DashScope 原生 API 端点
    api_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis"

    print(f"[INFO] Generating image {image_index} with model: {DASHSCOPE_MODEL}")
    print(f"[INFO] API endpoint: {api_url}")

    try:
        async with httpx.AsyncClient(timeout=180) as client:
            # 第一步：提交任务（异步模式）
            response = await client.post(
                api_url,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
                    "X-DashScope-Async": "enable"  # 异步模式
                },
                json={
                    "model": DASHSCOPE_MODEL,
                    "input": {
                        "prompt": prompt
                    },
                    "parameters": {
                        "size": "1024*1024",
                        "n": 1
                    }
                }
            )

            print(f"[INFO] DashScope API response status: {response.status_code}")

            if response.status_code != 200:
                print(f"[WARN] DashScope API returned status {response.status_code}")
                print(f"[WARN] Response: {response.text[:500]}")
                return None

            result = response.json()
            print(f"[DEBUG] Task submission response: {json.dumps(result, ensure_ascii=False)[:500]}")

            # 获取任务 ID
            task_id = result.get("output", {}).get("task_id")
            if not task_id:
                print(f"[WARN] No task_id in response")
                return None

            print(f"[INFO] Task submitted, task_id: {task_id}")

            # 第二步：轮询任务状态
            task_url = f"https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"
            max_attempts = 60  # 最多等待 60 次

            for attempt in range(max_attempts):
                await anyio.sleep(2)  # 每 2 秒检查一次

                task_response = await client.get(
                    task_url,
                    headers={
                        "Authorization": f"Bearer {DASHSCOPE_API_KEY}"
                    }
                )

                if task_response.status_code != 200:
                    print(f"[WARN] Task query failed: {task_response.status_code}")
                    continue

                task_result = task_response.json()
                task_status = task_result.get("output", {}).get("task_status")

                print(f"[INFO] Task status ({attempt + 1}/{max_attempts}): {task_status}")

                if task_status == "SUCCEEDED":
                    # 获取图片 URL
                    results = task_result.get("output", {}).get("results", [])
                    if results and "url" in results[0]:
                        image_url = results[0]["url"]
                        print(f"[INFO] Image URL: {image_url[:100]}...")

                        # 下载图片
                        img_response = await client.get(image_url, timeout=60)
                        if img_response.status_code == 200:
                            image_path = OUTPUT_DIR / f"image_{image_index}.png"
                            with open(image_path, "wb") as f:
                                f.write(img_response.content)
                            print(f"[INFO] Image {image_index} saved to {image_path}")
                            return str(image_path)
                        else:
                            print(f"[WARN] Failed to download image: {img_response.status_code}")
                    return None

                elif task_status == "FAILED":
                    error_msg = task_result.get("output", {}).get("message", "Unknown error")
                    print(f"[ERROR] Task failed: {error_msg}")
                    return None

                elif task_status in ["PENDING", "RUNNING"]:
                    continue
                else:
                    print(f"[WARN] Unknown task status: {task_status}")

            print(f"[WARN] Task timed out after {max_attempts} attempts")
            return None

    except Exception as e:
        print(f"[ERROR] Image generation failed: {e}")
        import traceback
        traceback.print_exc()
        return None


# ============================================================
# 图片生成函数（Gemini 3 Pro Image - 通过 yunwu.ai 代理）
# ============================================================
async def generate_image_gemini(prompt: str, image_index: int) -> str | None:
    """调用 Gemini 3 Pro Image API 生成图片"""
    if not GEMINI_API_KEY:
        print(f"[WARN] GEMINI_API_KEY not set, skipping image {image_index}")
        return None

    # Gemini API 端点
    api_url = f"{GEMINI_BASE_URL}/{GEMINI_MODEL}:generateContent"

    print(f"[INFO] Generating image {image_index} with Gemini model: {GEMINI_MODEL}")
    print(f"[INFO] API endpoint: {api_url}")

    try:
        async with httpx.AsyncClient(timeout=180) as client:
            response = await client.post(
                api_url,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {GEMINI_API_KEY}"
                },
                json={
                    "contents": [
                        {
                            "parts": [
                                {"text": prompt}
                            ]
                        }
                    ],
                    "generationConfig": {
                        "responseModalities": ["TEXT", "IMAGE"]
                    }
                }
            )

            print(f"[INFO] Gemini API response status: {response.status_code}")

            if response.status_code != 200:
                print(f"[WARN] Gemini API returned status {response.status_code}")
                print(f"[WARN] Response: {response.text[:500]}")
                return None

            result = response.json()
            print(f"[DEBUG] Gemini response: {json.dumps(result, ensure_ascii=False)[:500]}")

            # 解析 Gemini 响应，查找图片数据
            candidates = result.get("candidates", [])
            if not candidates:
                print(f"[WARN] No candidates in Gemini response")
                return None

            parts = candidates[0].get("content", {}).get("parts", [])
            for part in parts:
                if "inlineData" in part:
                    inline_data = part["inlineData"]
                    mime_type = inline_data.get("mimeType", "image/png")
                    image_b64 = inline_data.get("data", "")

                    if image_b64:
                        # 解码并保存图片
                        image_bytes = base64.b64decode(image_b64)
                        ext = "png" if "png" in mime_type else "jpg"
                        image_path = OUTPUT_DIR / f"image_{image_index}.{ext}"
                        with open(image_path, "wb") as f:
                            f.write(image_bytes)
                        print(f"[INFO] Image {image_index} saved to {image_path}")
                        return str(image_path)

            print(f"[WARN] No image data found in Gemini response")
            return None

    except Exception as e:
        print(f"[ERROR] Gemini image generation failed: {e}")
        import traceback
        traceback.print_exc()
        return None


# ============================================================
# PDF 文本提取
# ============================================================
def extract_pdf_text(pdf_path: str) -> str:
    """从 PDF 文件中提取文本"""
    try:
        from PyPDF2 import PdfReader

        reader = PdfReader(pdf_path)
        text_parts = []

        for page_num, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                text_parts.append(f"--- Page {page_num + 1} ---\n{text}")

        full_text = "\n\n".join(text_parts)
        print(f"[INFO] Extracted {len(full_text)} characters from {len(reader.pages)} pages")
        return full_text

    except Exception as e:
        print(f"[ERROR] PDF extraction failed: {e}")
        return ""


# ============================================================
# Markdown 转 HTML/PDF
# ============================================================
def convert_md_to_html(md_content: str, html_file: Path, title: str = "论文解读") -> bool:
    """将 Markdown 内容转换为 HTML 文件"""
    try:
        import markdown

        # 配置 Markdown 扩展
        extensions = [
            'markdown.extensions.extra',
            'markdown.extensions.codehilite',
            'markdown.extensions.toc',
            'markdown.extensions.tables',
            'markdown.extensions.fenced_code'
        ]

        # 转换为 HTML
        html_content = markdown.markdown(md_content, extensions=extensions)

        # HTML 模板 (使用 Noto Sans CJK SC 支持中文)
        html_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        @font-face {{
            font-family: 'Noto Sans CJK SC';
            src: local('Noto Sans CJK SC'), local('NotoSansCJK-Regular');
        }}
        body {{
            font-family: 'Noto Sans CJK SC', 'Noto Sans SC', 'Microsoft YaHei', 'SimHei', sans-serif;
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
            font-family: 'Noto Sans CJK SC', 'Noto Sans SC', 'Microsoft YaHei', 'SimHei', sans-serif;
            color: #1a237e;
            border-bottom: 3px solid #3f51b5;
            padding-bottom: 10px;
            margin-top: 40px;
            font-size: 2em;
        }}
        h2 {{
            font-family: 'Noto Sans CJK SC', 'Noto Sans SC', 'Microsoft YaHei', 'SimHei', sans-serif;
            color: #283593;
            border-left: 4px solid #3f51b5;
            padding-left: 15px;
            margin-top: 35px;
            font-size: 1.5em;
        }}
        h3 {{
            font-family: 'Noto Sans CJK SC', 'Noto Sans SC', 'Microsoft YaHei', 'SimHei', sans-serif;
            color: #3949ab;
            margin-top: 25px;
            font-size: 1.2em;
        }}
        p {{
            text-align: justify;
            margin: 15px 0;
        }}
        code {{
            background-color: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: Consolas, Monaco, monospace;
            font-size: 0.9em;
            color: #e91e63;
        }}
        pre {{
            background-color: #2b2b2b;
            color: #f8f8f2;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
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
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #3f51b5;
            color: white;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        img {{
            max-width: 100%;
            height: auto;
            display: block;
            margin: 20px auto;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}
        hr {{
            border: none;
            border-top: 2px solid #e0e0e0;
            margin: 30px 0;
        }}
        strong {{
            color: #d32f2f;
        }}
        footer {{
            margin-top: 60px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            text-align: center;
            color: #999;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
<div class="container">
{html_content}
<footer>
    <p>本解读由 GitHub Actions + Claude Agent SDK + 通义万相 自动生成</p>
</footer>
</div>
</body>
</html>"""

        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_template)

        print(f"[INFO] HTML file generated: {html_file}")
        return True

    except Exception as e:
        print(f"[ERROR] HTML conversion failed: {e}")
        return False


def convert_html_to_pdf(html_file: Path, pdf_file: Path) -> bool:
    """将 HTML 文件转换为 PDF（使用 WeasyPrint，支持中文）"""
    try:
        from weasyprint import HTML, CSS
        from weasyprint.text.fonts import FontConfiguration

        print(f"[INFO] Converting HTML to PDF using WeasyPrint...")

        # 配置字体
        font_config = FontConfiguration()

        # 读取 HTML 文件
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()

        # 为 PDF 优化（移除渐变背景，调整样式）
        pdf_html = html_content.replace(
            'background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);',
            'background: white;'
        )

        # 将相对图片路径转换为绝对路径
        html_dir = html_file.parent.absolute()
        import re
        # 匹配 src="image_X.png" 或 src='image_X.png'
        pdf_html = re.sub(
            r'src=["\']([^"\']+\.png)["\']',
            lambda m: f'src="file://{html_dir / m.group(1)}"',
            pdf_html
        )
        print(f"[INFO] Image base path: {html_dir}")

        # 额外的 PDF 样式
        pdf_css = CSS(string='''
            @page {
                size: A4;
                margin: 2cm;
            }
            body {
                font-family: "Noto Sans CJK SC", "Noto Sans SC", "SimHei", sans-serif;
            }
        ''', font_config=font_config)

        # 生成 PDF
        HTML(string=pdf_html).write_pdf(
            pdf_file,
            stylesheets=[pdf_css],
            font_config=font_config
        )

        print(f"[INFO] PDF file generated: {pdf_file}")
        return True

    except Exception as e:
        print(f"[ERROR] PDF conversion failed: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================
# 主执行函数（使用 Claude Agent SDK）
# ============================================================
async def run_paper_reader():
    """使用 Claude Agent SDK 执行论文解读"""

    # 验证环境变量
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("[ERROR] ANTHROPIC_API_KEY environment variable is not set")
        sys.exit(1)

    if not os.environ.get("ANTHROPIC_BASE_URL"):
        print("[WARN] ANTHROPIC_BASE_URL not set, will use default Anthropic API")

    if not PAPER_PATH or not Path(PAPER_PATH).exists():
        print(f"[ERROR] Paper file not found: {PAPER_PATH}")
        sys.exit(1)

    # 创建输出目录
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 提取 PDF 文本
    print(f"[INFO] Reading paper: {PAPER_PATH}")
    pdf_text = extract_pdf_text(PAPER_PATH)

    if not pdf_text:
        print("[ERROR] Failed to extract text from PDF")
        sys.exit(1)

    # 限制文本长度（避免超出 token 限制）
    max_chars = 100000
    if len(pdf_text) > max_chars:
        print(f"[WARN] Text truncated from {len(pdf_text)} to {max_chars} characters")
        pdf_text = pdf_text[:max_chars]

    start_time = datetime.now()

    # 构建提示词
    user_prompt = f"""请阅读以下学术论文内容，并按照"黄叔风格"生成一篇通俗易懂的中文解读文章。

论文内容:
```
{pdf_text}
```

请生成完整的 Markdown 格式解读文章，包含所有章节。"""

    # 使用 Claude Agent SDK
    print(f"[INFO] Calling Claude Agent SDK (model: {ANTHROPIC_MODEL})...")
    print(f"[INFO] Base URL: {os.environ.get('ANTHROPIC_BASE_URL', 'default')}")

    try:
        from claude_agent_sdk import query

        full_response = []
        async for message in query(
            prompt=user_prompt,
            system=SYSTEM_PROMPT,
            model=ANTHROPIC_MODEL,
            max_tokens=8000
        ):
            # 处理不同类型的消息
            if hasattr(message, 'content'):
                content = message.content
                if isinstance(content, list):
                    for block in content:
                        if hasattr(block, 'text'):
                            full_response.append(block.text)
                else:
                    full_response.append(str(content))
            elif hasattr(message, 'text'):
                full_response.append(message.text)
            elif hasattr(message, 'result'):
                full_response.append(str(message.result))

        explanation = "\n".join(full_response)

        if not explanation or len(explanation) < 100:
            print("[WARN] Agent SDK returned empty/short response, trying direct API...")
            explanation = await call_api_direct(user_prompt)

    except ImportError as e:
        print(f"[WARN] Claude Agent SDK not available ({e}), using direct API...")
        explanation = await call_api_direct(user_prompt)
    except Exception as e:
        print(f"[WARN] Agent SDK error ({e}), falling back to direct API...")
        explanation = await call_api_direct(user_prompt)

    # 计算处理时间
    processing_time = (datetime.now() - start_time).total_seconds()

    # 生成配图（优先使用 Gemini，备用 DashScope）
    image_status = "未生成"
    generated_images = []

    if GEMINI_API_KEY:
        print("[INFO] Generating images with Gemini 3 Pro Image...")
        # Gemini 擅长生成带文字的信息图
        image_prompts = [
            "Create an informative infographic about the Transformer architecture in deep learning. Include a visual diagram showing: 1) Input embeddings 2) Multi-head attention mechanism 3) Feed-forward layers 4) Output. Use clean modern design with blue and white colors. Add clear labels in English.",
            "Create a visual summary diagram showing the key innovation of 'Attention Is All You Need' paper. Illustrate how self-attention works: Query, Key, Value vectors connecting words in a sentence. Use professional scientific illustration style with annotations."
        ]

        for i, prompt in enumerate(image_prompts):
            img_path = await generate_image_gemini(prompt, i + 1)
            if img_path:
                generated_images.append(img_path)

        if generated_images:
            image_status = f"成功 ({len(generated_images)}张, Gemini)"
        else:
            image_status = "Gemini 失败"

    # 如果 Gemini 失败或未配置，尝试 DashScope
    if not generated_images and DASHSCOPE_API_KEY:
        print("[INFO] Falling back to DashScope (通义万相)...")
        image_prompts = [
            "abstract scientific visualization, neural network concept art, flowing data streams and connections, blue and purple gradient, modern minimalist style, clean geometric shapes",
            "futuristic knowledge concept illustration, glowing nodes and pathways, deep learning visualization, technological aesthetic, dark blue background with bright accents"
        ]

        for i, prompt in enumerate(image_prompts):
            img_path = await generate_image_dashscope(prompt, i + 1)
            if img_path:
                generated_images.append(img_path)

        if generated_images:
            image_status = f"成功 ({len(generated_images)}张, DashScope)"
        else:
            image_status = "失败（API 错误）"

    if not GEMINI_API_KEY and not DASHSCOPE_API_KEY:
        print("[INFO] DASHSCOPE_API_KEY not set, skipping image generation")

    # 添加元数据
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    metadata = f"""

---

**元数据**
📄 论文文件: `{PAPER_PATH}`
⏱️ 处理时长: {processing_time:.1f}秒
🖼️ 配图生成: {image_status}
🤖 生成模型: {ANTHROPIC_MODEL} (via Claude Agent SDK)
📅 生成时间: {datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")}

---

*本解读由 GitHub Actions + Claude Agent SDK + 通义万相 自动生成*
"""

    # 如果有图片，在文章末尾添加图片引用
    image_section = ""
    if generated_images:
        image_section = "\n\n---\n\n## 配图\n\n"
        for i, img_path in enumerate(generated_images):
            img_name = Path(img_path).name
            image_section += f"![配图{i+1}]({img_name})\n\n"

    final_output = explanation + image_section + metadata

    # 保存 Markdown 文件
    md_file = OUTPUT_DIR / f"paper-explanation-{timestamp}.md"
    with open(md_file, "w", encoding="utf-8") as f:
        f.write(final_output)
    print(f"[SUCCESS] Markdown saved to: {md_file}")

    # 转换为 HTML
    html_file = OUTPUT_DIR / f"paper-explanation-{timestamp}.html"
    convert_md_to_html(final_output, html_file, "论文解读")

    # 转换为 PDF
    pdf_file = OUTPUT_DIR / f"paper-explanation-{timestamp}.pdf"
    convert_html_to_pdf(html_file, pdf_file)

    print(f"[INFO] Processing time: {processing_time:.1f}s")
    print(f"[INFO] Output files:")
    print(f"       - Markdown: {md_file}")
    print(f"       - HTML: {html_file}")
    print(f"       - PDF: {pdf_file}")

    return md_file


async def call_api_direct(prompt: str) -> str:
    """直接调用 API（备用方案，当 Agent SDK 不可用时）"""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    base_url = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com")

    # 确保 base_url 格式正确
    if not base_url.endswith("/v1/messages"):
        base_url = base_url.rstrip("/") + "/v1/messages"

    try:
        async with httpx.AsyncClient(timeout=180) as client:
            response = await client.post(
                base_url,
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01"
                },
                json={
                    "model": ANTHROPIC_MODEL,
                    "max_tokens": 8000,
                    "system": SYSTEM_PROMPT,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ]
                }
            )

            if response.status_code == 200:
                result = response.json()
                return result["content"][0]["text"]
            else:
                print(f"[ERROR] API returned status {response.status_code}: {response.text}")
                return f"API 调用失败: {response.status_code}"

    except Exception as e:
        print(f"[ERROR] Direct API call failed: {e}")
        return f"API 调用异常: {e}"


# ============================================================
# 入口点
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("       Paper Reader - Cloud Execution Script")
    print("       Using Claude Agent SDK + 通义万相")
    print("       Output: Markdown + HTML + PDF")
    print("=" * 60)
    print()

    anyio.run(run_paper_reader)
