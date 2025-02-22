import subprocess
import requests
import json
import re
import sys

import threading

from PIL import Image
import pyautogui
import tkinter as tk

def query_ollama(prompt):
    """
    向 Ollama 模型发送请求，获取结构化数据。
    """
    url = "http://localhost:11434/api/generate"
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": "deepseek-r1:14b",
        "prompt": prompt
    }


    response = requests.post(url, headers=headers, data=json.dumps(payload))
    response.raise_for_status()  # 如果响应状态码不是 200，会抛出异常

    # 打印返回的原始响应内容
    print("Raw Response:", response.text)

    model_result = extract_responses(response.text)

    print("model result:", model_result)

    # 从返回结果中提取出目标的JSON结构
    structured_data = extract_json(model_result)


    # 尝试解析 JSON
    return structured_data

def extract_responses(raw_response):
    """
    从多个响应中提取并按顺序拼接 `response` 字段。
    """
    responses = []
    for line in raw_response.split('\n'):
        if line.strip():
            try:
                # 尝试解析每一行的JSON数据
                response_data = json.loads(line)
                # 如果有 `response` 字段，添加到结果列表
                if 'response' in response_data:
                    responses.append(response_data['response'])
            except json.JSONDecodeError:
                continue  # 如果解析错误，跳过该行

    # 将所有的 `response` 字段按顺序拼接成一个字符串
    return ''.join(responses)

def extract_json(model_result):
    """
    从模型返回的文本中提取结构化的JSON数据。
    """
    # 使用正则表达式提取 JSON 格式的数据
    match = re.search(r'\{.*?}', model_result, re.DOTALL)
    if match:
        try:
            # 输出匹配到的部分
            print("Matched JSON string:", match.group(0))
            # 尝试将提取的字符串解析为 JSON 数据
            json_data = json.loads(match.group(0))
            return json_data
        except json.JSONDecodeError:
            print("Error parsing JSON.")
            return None
    return None


def call_client_script(model_response):
    """
    调用 client.py 并传递 model_response 作为参数。
    """
    # 将 model_response 转换为字符串格式
    model_response_str = json.dumps(model_response)

    # 调用 client.py，并传递 model_response_str 作为参数
    result = subprocess.run(
        ['python', 'client.py', model_response_str],
        stdout=sys.stdout,  # 将 client.py 的 stdout 输出到 PyCharm 控制台
        stderr=sys.stderr,  # 将 client.py 的 stderr 输出到 PyCharm 控制台
        text=True,
        encoding = 'utf-8'  # 显式指定使用 utf-8 编码
    )

    print("Client Script Output:", result.stdout)
    if result.stderr:
        print("Client Script Error:", result.stderr)



# 获取系统 DPI 设置
def get_dpi():
    root = tk.Tk()
    dpi = root.winfo_fpixels('1i')  # 获取每英寸的像素数
    root.destroy()

    print(f"系统 DPI: {dpi}")

    return dpi


def capture_screen(image_path):
    """截取当前屏幕并保存为图像文件"""
    # 获取系统DPI
    dpi = get_dpi()
    print(f"系统 DPI: {dpi}")

    # 获取当前屏幕截图
    screenshot = pyautogui.screenshot()

    # 根据DPI调整截图的大小
    if dpi != 96:  # 96 DPI为默认标准
        scale_factor = dpi / 96
        new_width = int(screenshot.width * scale_factor)
        new_height = int(screenshot.height * scale_factor)

        # 缩放图像
        screenshot = screenshot.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # 保存截图
    screenshot.save(image_path)
    print(f"屏幕截图已保存至: {image_path}")



def main():
    """
    主程序，获取用户输入，查询模型，解析响应，并执行相应的操作。
    """
    # 获取用户输入
    user_input = input("请输入操作指令（例如，点击回收站图标）：")
    prompt = f"""
    你是一个智能助手，请根据以下输入返回结构化数据（JSON 格式）：
    - "action"：操作类型（例如，click，double_click）
    - "target"：目标元素（例如，recycle_bin, start_button）

    输入：'{user_input}'

    返回格式：
    {{
        "action": "click",
        "target": "回收站"
    }}
    
    另外。你需要知道打开某个程序一般情况下对应的操作类型是双击
    并且，如果如果是应用程序的名字不要做任何修改
    """

    # 获取模型返回的结构化数据
    model_response = query_ollama(prompt)

    # 打印完整的返回结果
    # 打印返回的结构化数据
    if model_response:
        print("Structured Result:", model_response)

        # 截取屏幕并保存
        image_path = r"D:\WallPaper\test.png"
        capture_screen(image_path)

        # 调用 client.py，并传递 model_response
        #call_client_script(model_response)

        # 在新线程中调用 client.py，并传递 model_response
        client_thread = threading.Thread(target=call_client_script, args=(model_response,))
        client_thread.start()

    else:
        print("未提取到有效的结构化数据。")


if __name__ == "__main__":
    main()
