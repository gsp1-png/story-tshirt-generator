"""
测试通义千问 API 是否可用。
跑这个脚本前确认：
1. .env 里有 DASHSCOPE_API_KEY
2. 已经 pip install dashscope python-dotenv
"""
import os
from dotenv import load_dotenv
import dashscope

# 从 .env 加载 API key
load_dotenv()
dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")

if not dashscope.api_key:
    raise RuntimeError("没找到 DASHSCOPE_API_KEY，检查 .env 文件")

# 调一次最便宜的对话，确认能通
response = dashscope.Generation.call(
    model="qwen-plus",
    messages=[
        {"role": "user", "content": "用一句话介绍《道德经》。"}
    ],
)

# 打印结果
if response.status_code == 200:
    print("✅ 通义千问连通成功")
    print("模型回复：", response.output.text)
else:
    print("❌ 调用失败")
    print("状态码：", response.status_code)
    print("错误信息：", response.message)