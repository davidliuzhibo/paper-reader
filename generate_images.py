#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用阿里云通义万相API生成配图
"""

import requests
import json
import time
import os

API_KEY = "sk-d044f39d8be848e898a81df4c5182444"
BASE_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis"

def generate_image(prompt, output_file):
    """Generate image using Aliyun Tongyi Wanxiang API"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "X-DashScope-Async": "enable"
    }

    payload = {
        "model": "wanx-v1",
        "input": {
            "prompt": prompt
        },
        "parameters": {
            "size": "1024*1024",
            "n": 1
        }
    }

    print(f"Generating image with prompt: {prompt[:80]}...")

    try:
        # Make API request
        response = requests.post(BASE_URL, headers=headers, json=payload, timeout=60)

        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:500]}")

        if response.status_code == 200:
            result = response.json()
            print(f"API Response: {json.dumps(result, indent=2, ensure_ascii=False)[:300]}")

            # Async mode: get task_id and poll
            if result.get("output"):
                task_id = result["output"].get("task_id")
                if task_id:
                    print(f"[INFO] Task submitted: {task_id}")

                    # Poll for completion
                    task_url = f"https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"
                    for attempt in range(20):  # Max 20 attempts (60 seconds)
                        time.sleep(3)
                        print(f"  Polling... ({attempt+1}/20)", end='\r')

                        task_response = requests.get(task_url, headers=headers, timeout=30)
                        if task_response.status_code == 200:
                            task_result = task_response.json()
                            status = task_result.get("output", {}).get("task_status")

                            if status == "SUCCEEDED":
                                print("\n[OK] Task completed!")
                                results = task_result["output"].get("results", [])
                                if results:
                                    image_url = results[0].get("url")
                                    if image_url:
                                        # Download image
                                        img_response = requests.get(image_url, timeout=30)
                                        with open(output_file, 'wb') as f:
                                            f.write(img_response.content)
                                        print(f"[OK] Image saved: {output_file}")
                                        return image_url
                            elif status == "FAILED":
                                print(f"\n[ERROR] Task failed: {task_result}")
                                return None

                    print("\n[WARN] Timeout waiting for task completion")
                    return None

        else:
            print(f"[ERROR] API error: {response.text}")
            return None

    except Exception as e:
        print(f"[ERROR] Exception: {e}")
        return None

def main():
    print("="*70)
    print("Aliyun Tongyi Wanxiang Image Generator")
    print("="*70)

    prompts = [
        ("Transformer architecture diagram with encoder and decoder",
         "transformer_architecture.jpg"),

        ("Attention mechanism flowchart showing Q, K, V, softmax process",
         "attention_mechanism.jpg"),

        ("Infographic summarizing Transformer paper contributions",
         "transformer_summary.jpg")
    ]

    for prompt, filename in prompts:
        print(f"\n[{filename}]")
        generate_image(prompt, filename)
        time.sleep(1)

    print("\n" + "="*70)
    print("Done")
    print("="*70)

if __name__ == "__main__":
    main()
