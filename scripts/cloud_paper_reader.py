#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
云端论文解读执行脚本
使用 Claude Agent SDK 调用 Claude 模型（通过 yunwu.ai 代理）
使用阿里通义万相 2.6 生成配图

环境变量（GitHub Secrets 配置）:
  - ANTHROPIC_API_KEY: yunwu.ai API 密钥
  - ANTHROPIC_BASE_URL: yunwu.ai API 端点
  - ANTHROPIC_MODEL: Claude 模型名称
  - DASHSCOPE_API_KEY: 阿里通义万相 API 密钥
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

# 阿里通义万相配置
DASHSCOPE_API_KEY = os.environ.get("DASHSCOPE_API_KEY")
DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DASHSCOPE_MODEL = "wanx2.1-t2i-turbo"  # 通义万相文生图模型

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
# 图片生成函数（阿里通义万相）
# ============================================================
async def generate_image_dashscope(prompt: str, image_index: int) -> str | None:
    """调用阿里通义万相 API 生成图片"""
    if not DASHSCOPE_API_KEY:
        print(f"[WARN] DASHSCOPE_API_KEY not set, skipping image {image_index}")
        return None

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            # 通义万相使用 OpenAI 兼容格式
            response = await client.post(
                f"{DASHSCOPE_BASE_URL}/images/generations",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {DASHSCOPE_API_KEY}"
                },
                json={
                    "model": DASHSCOPE_MODEL,
                    "prompt": prompt,
                    "n": 1,
                    "size": "1024x1024"
                }
            )

            if response.status_code == 200:
                result = response.json()
                if "data" in result and len(result["data"]) > 0:
                    image_data = result["data"][0]

                    # 检查返回的是 URL 还是 base64
                    if "url" in image_data:
                        # 下载图片并保存
                        img_response = await client.get(image_data["url"])
                        if img_response.status_code == 200:
                            image_path = OUTPUT_DIR / f"image_{image_index}.png"
                            with open(image_path, "wb") as f:
                                f.write(img_response.content)
                            print(f"[INFO] Image {image_index} saved to {image_path}")
                            return str(image_path)
                    elif "b64_json" in image_data:
                        # 直接保存 base64 数据
                        image_bytes = base64.b64decode(image_data["b64_json"])
                        image_path = OUTPUT_DIR / f"image_{image_index}.png"
                        with open(image_path, "wb") as f:
                            f.write(image_bytes)
                        print(f"[INFO] Image {image_index} saved to {image_path}")
                        return str(image_path)

                print(f"[WARN] Unexpected API response format for image {image_index}")
                return None
            else:
                print(f"[WARN] DashScope API returned status {response.status_code}: {response.text}")
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

    # 生成配图（使用通义万相）
    image_status = "未生成"
    if DASHSCOPE_API_KEY:
        print("[INFO] Generating images with DashScope (通义万相)...")
        image_prompts = [
            "学术论文核心概念可视化插图，现代简洁的教育风格，清晰的图形和标注，蓝色科技感配色",
            "学术研究成果信息图，包含3-5个要点的总结图表，现代信息图表风格，专业商务感"
        ]

        generated_images = []
        for i, prompt in enumerate(image_prompts):
            img_path = await generate_image_dashscope(prompt, i + 1)
            if img_path:
                generated_images.append(img_path)

        if generated_images:
            image_status = f"成功 ({len(generated_images)}张)"
        else:
            image_status = "失败（API 错误）"
    else:
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

    final_output = explanation + metadata

    # 保存输出文件
    output_file = OUTPUT_DIR / f"paper-explanation-{timestamp}.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(final_output)

    print(f"[SUCCESS] Output saved to: {output_file}")
    print(f"[INFO] Processing time: {processing_time:.1f}s")
    print(f"[INFO] Output length: {len(final_output)} characters")

    return output_file


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
    print("=" * 60)
    print()

    anyio.run(run_paper_reader)
