
"""
模块：参考图风格分析

输入：
    用户上传的参考图

输出：
    style_anchor（统一风格描述）
"""

import os
import json
import base64

from dotenv import load_dotenv
import dashscope

load_dotenv()

dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")


def encode_image(image_path: str) -> str:
    """
    图片转 base64
    """

    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


SYSTEM_PROMPT = """
你是一位顶级视觉艺术风格分析师。

用户会上传一张图片。

你的任务是：

1. 分析图片中的：
- 艺术风格
- 色彩体系
- 构图方式
- 光影风格
- 线条风格
- 材质质感
- 情绪氛围

2. 最终输出一个统一风格锚点 style_anchor。

要求：

- 使用简洁视觉关键词
- 不超过 40 字
- 适合作为 AI 绘图 prompt 前缀
- 不要解释
- 不要分点
- 不要输出 JSON
- 直接输出风格短句

例如：

赛博朋克霓虹、低饱和蓝紫色调、粗颗粒漫画质感、电影感边缘光

或：

浮世绘木版画风格、靛蓝主调、平涂留白、粗线条轮廓
"""


def extract_style(image_path: str) -> str:
    """
    从参考图提取统一风格描述
    """

    image_base64 = encode_image(image_path)

    response = dashscope.MultiModalConversation.call(

        model="qwen-vl-max",

        messages=[
            {
                "role": "system",
                "content": [{"text": SYSTEM_PROMPT}],
            },

            {
                "role": "user",
                "content": [

                    {
                        "image": f"data:image/png;base64,{image_base64}"
                    },

                    {
                        "text": "请分析这张图的视觉风格"
                    },
                ],
            },
        ],
    )

    if response.status_code != 200:

        raise RuntimeError(
            f"风格分析失败 | "
            f"{response.status_code} | "
            f"{response.message}"
        )

    result = response.output.choices[0].message.content[0]["text"]

    return result.strip()

