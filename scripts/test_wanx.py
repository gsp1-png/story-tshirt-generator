"""
测试通义万相 API 是否可用。
会生成一张图，存到 outputs/test_wanx2.png
"""
import os
from pathlib import Path
from dotenv import load_dotenv
import dashscope
from dashscope import ImageSynthesis
import requests

load_dotenv()
dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")

if not dashscope.api_key:
    raise RuntimeError("没找到 DASHSCOPE_API_KEY")

print("⏳ 正在生成图片，约 10-30 秒...")

response = ImageSynthesis.call(
    model="wanx2.1-t2i-turbo",
    prompt="一副有很多颜色的图",
    n=1,
    size="1024*1024",
)

if response.status_code == 200:
    # 拿到图片 URL，下载到本地
    img_url = response.output.results[0].url
    print(f"✅ 通义万相连通成功")
    print(f"图片 URL: {img_url}")

    # 下载
    Path("outputs").mkdir(exist_ok=True)
    img_data = requests.get(img_url).content
    out_path = Path("outputs") / "test_wanx2.png"
    out_path.write_bytes(img_data)
    print(f"✅ 图片已保存到: {out_path.resolve()}")
else:
    print("❌ 调用失败")
    print("状态码：", response.status_code)
    print("错误信息：", response.message)