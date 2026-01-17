#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
云端论文解读执行脚本
通过 yunwu.ai 第三方 API 调用 Claude 模型

环境变量:
  - YUNWU_API_KEY: yunwu.ai API 密钥（用于 Claude 和图片生成）
  - YUNWU_IMAGE_API_KEY: 图片生成 API 密钥（可选，如果与 Claude API 不同）
  - PAPER_PATH: 论文文件路径
"""

import os
import sys
import json
import asyncio
from datetime import datetime
from pathlib import Path

import anyio
import httpx


# ============================================================
# 配置
# ============================================================
# Claude API 配置（通过 yunwu.ai 代理）
YUNWU_API_KEY = os.environ.get("YUNWU_API_KEY")
YUNWU_API_BASE = "https://yunwu.ai/v1/messages"
CLAUDE_MODEL = "claude-opus-4-5-20251101"

# 图片生成 API 配置
YUNWU_IMAGE_API_KEY = os.environ.get("YUNWU_IMAGE_API_KEY", os.environ.get("YUNWU_API_KEY"))
IMAGE_API_ENDPOINT = "https://yunwu.ai/v1beta/models/gemini-3-pro-image-preview:generateContent"
IMAGE_API_TIMEOUT = 30

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
# 图片生成函数
# ============================================================
async def generate_image(prompt: str, image_index: int) -> str | None:
    """调用 Yunwu API 生成图片"""
    if not YUNWU_IMAGE_API_KEY:
        print(f"[WARN] YUNWU_IMAGE_API_KEY not set, skipping image {image_index}")
        return None

    try:
        async with httpx.AsyncClient(timeout=IMAGE_API_TIMEOUT) as client:
            response = await client.post(
                IMAGE_API_ENDPOINT,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {YUNWU_IMAGE_API_KEY}"
                },
                json={
                    "contents": [{
                        "parts": [{
                            "text": prompt
                        }]
                    }],
                    "generationConfig": {
                        "temperature": 0.7,
                        "maxOutputTokens": 2048
                    }
                }
            )

            if response.status_code == 200:
                result = response.json()
                # 解析返回的图片 URL（根据实际 API 响应格式调整）
                if "candidates" in result:
                    candidate = result["candidates"][0]
                    if "content" in candidate and "parts" in candidate["content"]:
                        for part in candidate["content"]["parts"]:
                            if "inlineData" in part:
                                # 如果返回 base64 数据，保存为文件
                                import base64
                                image_data = base64.b64decode(part["inlineData"]["data"])
                                image_path = OUTPUT_DIR / f"image_{image_index}.png"
                                with open(image_path, "wb") as f:
                                    f.write(image_data)
                                return str(image_path)
                            elif "text" in part:
                                # 如果返回 URL
                                return part.get("fileData", {}).get("fileUri", "")
                print(f"[WARN] Unexpected API response format for image {image_index}")
                return None
            else:
                print(f"[WARN] Image API returned status {response.status_code}")
                return None

    except Exception as e:
        print(f"[ERROR] Image generation failed: {e}")
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
# 主执行函数（使用 yunwu.ai 第三方 API）
# ============================================================
async def run_paper_reader():
    """通过 yunwu.ai 调用 Claude API 执行论文解读"""

    # 验证环境变量
    if not YUNWU_API_KEY:
        print("[ERROR] YUNWU_API_KEY environment variable is not set")
        sys.exit(1)

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

    # 调用 yunwu.ai Claude API
    print(f"[INFO] Calling Claude API via yunwu.ai (model: {CLAUDE_MODEL})...")
    explanation = await call_yunwu_claude_api(user_prompt)

    # 计算处理时间
    processing_time = (datetime.now() - start_time).total_seconds()

    # 生成配图（尝试）
    image_status = "未生成"
    if YUNWU_IMAGE_API_KEY:
        print("[INFO] Generating images...")
        image_prompts = [
            "创建一张教育性插图，展示这篇论文的核心概念。用简洁的图形和标注说明关键机制。风格：现代、清晰、适合科普文章。",
            "创建一张信息图，总结论文的主要发现。包含3-5个要点，每个要点用图标和简短文字说明。风格：现代信息图表。"
        ]

        generated_images = []
        for i, prompt in enumerate(image_prompts):
            img_path = await generate_image(prompt, i + 1)
            if img_path:
                generated_images.append(img_path)

        if generated_images:
            image_status = f"成功 ({len(generated_images)}张)"
        else:
            image_status = "失败（API 错误）"

    # 添加元数据
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    metadata = f"""

---

**元数据**
📄 论文文件: `{PAPER_PATH}`
⏱️ 处理时长: {processing_time:.1f}秒
🖼️ 配图生成: {image_status}
🤖 生成模型: {CLAUDE_MODEL} (via yunwu.ai)
📅 生成时间: {datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")}

---

*本解读由 GitHub Actions + yunwu.ai Claude API 自动生成*
"""

    final_output = explanation + metadata

    # 保存输出文件
    output_file = OUTPUT_DIR / f"paper-explanation-{timestamp}.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(final_output)

    print(f"[SUCCESS] Output saved to: {output_file}")
    print(f"[INFO] Processing time: {processing_time:.1f}s")
    print(f"[INFO] Output length: {len(final_output)} characters")

    return output_file


async def call_yunwu_claude_api(prompt: str) -> str:
    """通过 yunwu.ai 调用 Claude API"""
    try:
        async with httpx.AsyncClient(timeout=180) as client:
            response = await client.post(
                YUNWU_API_BASE,
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": YUNWU_API_KEY,
                    "anthropic-version": "2023-06-01"
                },
                json={
                    "model": CLAUDE_MODEL,
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
        print(f"[ERROR] yunwu.ai API call failed: {e}")
        return f"API 调用异常: {e}"


# ============================================================
# 入口点
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("       Paper Reader - Cloud Execution Script")
    print("       Using yunwu.ai Claude API")
    print("=" * 60)
    print()

    anyio.run(run_paper_reader)
