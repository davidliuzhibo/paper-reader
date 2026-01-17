import os
import sys
import requests
import json
import base64
import time

def get_api_key():
    # 1. 尝试从环境变量获取
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        return api_key.strip()
    
    # 2. 尝试从同目录下的 key.txt 获取
    current_dir = os.path.dirname(os.path.abspath(__file__))
    key_file = os.path.join(current_dir, "key.txt")
    
    if os.path.exists(key_file):
        try:
            with open(key_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content and "PASTE" not in content: # 简单的检查，防止读取到占位符
                    return content
        except Exception:
            pass
            
    return None

import copy

import copy

def generate_image(prompt, api_key):
    # 用户提供的正确 Image Preview 端点
    base_url = "https://yunwu.ai/v1beta/models/gemini-3-pro-image-preview:generateContent"
    url = f"{base_url}?key={api_key}"
    
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        
        if response.status_code != 200:
            return f"❌ 请求失败 (Status {response.status_code})\n返回内容: {response.text}"
            
        result = response.json()
        
        # 尝试提取图片 (更加鲁棒的查找方式)
        b64_data = None
        try:
             # REST API 返回的字段通常是驼峰命名 inlineData
             if 'candidates' in result and result['candidates']:
                 parts = result['candidates'][0]['content']['parts']
                 for part in parts:
                     # 优先检查 inlineData (标准 REST)
                     if 'inlineData' in part:
                         b64_data = part['inlineData']['data']
                         break
                     # 兼容旧代码或其他格式
                     if 'inline_data' in part:
                         b64_data = part['inline_data']['data']
                         break
        except Exception as e:
            print(f"DEBUG: Parsing error: {e}")
            pass

        if b64_data:
            try:
                # 确保 pic 文件夹存在
                current_dir = os.path.dirname(os.path.abspath(__file__))
                pic_dir = os.path.join(current_dir, "pic")
                if not os.path.exists(pic_dir):
                    os.makedirs(pic_dir)

                # 保存图片
                timestamp = int(time.time())
                filename = f"image_{timestamp}.jpeg"
                filepath = os.path.join(pic_dir, filename)
                
                with open(filepath, "wb") as f:
                    f.write(base64.b64decode(b64_data))
                
                return f"✅ 图片已生成！\n保存在: {filepath}"
            except Exception as e:
                return f"❌ 保存图片失败: {e}"
        else:
            # 如果没找到图片，为了不刷屏，我们只打印 key 的结构和简要信息
            return f"❌ 未找到图片数据。\nResponse keys: {result.keys()}\nCandidates: {json.dumps(result.get('candidates', []), indent=2)[:500]}..."

    except Exception as e:
        return f"❌ 发生异常: {e}"

def main():
    api_key = get_api_key()
    
    if not api_key:
        print("Error: Could not find API Key.")
        print("请在 key.txt 中填入您的 Key。")
        return

    # 文本对话的配置
    text_base_url = "https://yunwu.ai/v1beta/models/gemini-3-pro-preview:generateContent"
    text_url = f"{text_base_url}?key={api_key}"

    def get_text_response(prompt, history=None):
        headers = {'Content-Type': 'application/json'}
        
        # 准备 Request Body
        request_contents = []
        if history:
            request_contents = copy.deepcopy(history)
            if request_contents[-1]['role'] == 'user':
                request_contents[-1]['parts'][0]['text'] += "\n(Only output the final result in Simplified Chinese. Do not output thoughts or reasoning process.)"
        else:
             request_contents = [{"parts": [{"text": prompt + "\n(Only output the final result in Simplified Chinese. Do not output thoughts or reasoning process.)"}]}]

        payload = {
            "contents": request_contents,
            "system_instruction": {
                "parts": [{"text": "You are a helpful assistant. You must answer in Chinese (Simplified). Do not output your thinking process (thoughts). 只输出最终结果。"}]
            }
        }
        
        try:
            response = requests.post(text_url, headers=headers, data=json.dumps(payload))
            if response.status_code != 200:
                return f"错误 ({response.status_code}): {response.text}"
            result = response.json()
            if 'candidates' in result and result['candidates']:
                 parts = result['candidates'][0]['content']['parts']
                 # 过滤掉思考过程 (thought)
                 final_text = ""
                 for part in parts:
                     # 检查是否包含 thought 字段 (REST API 可能返回 thought: True 或类似)
                     # 目前观察到 thoughts 可能会在单独的 part 或者是 text 的一部分
                     # 如果 part 中只有 text
                     if 'text' in part:
                         val = part['text']
                         # 简单的启发式过滤: 思考过程通常很长且是英文，且在第一部分（如果有多个部分）
                         # 或者如果有 'thought': True 标志
                         if part.get('thought', False):
                             continue
                             
                         # 如果这里包含了 Thinking Process... 也可以手动过滤
                         # 但现在主要依赖 API 结构。如果返回了多个 part，我们假设只有最后一个是最终回答？
                         # 或者我们拼接所有看起来像中文的内容？
                         # 让我们先简单拼接，但如果发现有多个 part，且第一个全是英文，可能是 thought
                         final_text += val
                 
                 # 二次清洗：如果包含 <thought> 标签
                 import re
                 final_text = re.sub(r'<thought>.*?</thought>', '', final_text, flags=re.DOTALL)
                 # 清洗 Thinking Process: ...
                 if "Thinking Process:" in final_text:
                     final_text = final_text.split("Thinking Process:")[-1]
                 
                 return final_text.strip()
            else:
                 return f"错误: 未收到有效回复。完整响应: {result}"
        except Exception as e:
            return f"发生异常: {e}"

    # CLI 启动
    if len(sys.argv) > 1:
        # 单次命令模式
        prompt = " ".join(sys.argv[1:])
        # 简单判断是否是画图请求
        if prompt.strip().startswith("画") or prompt.strip().startswith("/draw"):
            print(generate_image(prompt, api_key))
        else:
            print(get_text_response(prompt))
    else:
        # 交互模式
        print(f"欢迎使用 Gemini 智能助手")
        print(f" - 聊天: 直接输入文字")
        print(f" - 画图: 输入 '画一只猫' 或 '/draw a cat'")
        print("-" * 50)
        
        history = []
        while True:
            try:
                user_input = input("您: ")
                if user_input.lower() in ['exit', 'quit', '退出']:
                    break
                
                # 判断是否是画图请求
                if user_input.strip().startswith("画") or user_input.strip().startswith("/draw"):
                    print("Gemini (Nano Banana) 正在绘图...", end="\r")
                    res_text = generate_image(user_input, api_key)
                    # 清除提示
                    print(" " * 30, end="\r")
                    print(f"\n{res_text}\n")
                    # 画图通常不计入对话历史，或者仅作为文本记录
                    history.append({"role": "user", "parts": [{"text": user_input}]})
                    history.append({"role": "model", "parts": [{"text": "（已生成图片）"}]})
                else:
                    # 正常对话
                    history.append({"role": "user", "parts": [{"text": user_input}]})
                    print("Gemini 正在思考...", end="\r")
                    res_text = get_text_response(user_input, history)
                    print(" " * 20, end="\r")
                    print(f"Gemini: {res_text}\n")
                    history.append({"role": "model", "parts": [{"text": res_text}]})
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"程序出错: {e}")

if __name__ == "__main__":
    main()
