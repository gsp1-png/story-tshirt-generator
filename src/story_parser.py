
"""
模块 1：故事拆解
输入：
    - 故事文本（str）
    - 可选风格偏好（str）

输出：
    {
      "style_anchor": "...",
      "front_prompt": "...",
      "back_prompt": "...",
      "sleeve_prompt": "...",
      "badge_prompt": "..."
    }
"""

import os
import json
from dotenv import load_dotenv
import dashscope

load_dotenv()
dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")


# ─────────────────────────────────────────────
# 核心 Prompt 模板
# ─────────────────────────────────────────────
SYSTEM_PROMPT = """
你是一位专注于服装印花设计的视觉创意总监。

你的任务是：
把用户提供的故事或诗文，
拆解成 4 个 T 恤版位的图像生成 prompt。

用户会上传一张参考图作为统一视觉风格锚点。

你不需要重新发明风格，
而是需要：

1. 分析参考图可能对应的视觉语言
2. 用简洁关键词总结该风格
3. 保证 4 个版位都适合在该风格下生成
4. 保证整体像同一套系列设计

规则：

1. 每个 prompt 必须是纯视觉描述
   不允许：
   - 人物对话
   - 剧情描述
   - 长句叙事

2. 四个版位风格必须统一：
   - 颜色
   - 笔触
   - 构图
   - 艺术语言

3. 各版位功能：

- front：
  主视觉，信息量最大，承载核心意象

- back：
  叙事延展，可加入少量设计文字

- sleeve：
  极简符号化，一个图标或短语

- badge：
  章印感，浓缩符号 + 短词

4. style_anchor：
   用 3~5 个关键词 + 一句话
   描述参考图风格

5. 输出必须是严格 JSON
   不允许任何额外解释

输出格式：

{
  "style_anchor": "...",
  "front_prompt": "...",
  "back_prompt": "...",
  "sleeve_prompt": "...",
  "badge_prompt": "..."
}
"""



def parse_story(
    story_text: str,
    style_anchor: str = "",
) -> dict:
    """
    把故事拆解为多版位图像 prompt
    """

    user_msg = f"故事原文：\n{story_text}"


    if style_anchor:
        user_msg += f"\n\n参考图风格：{style_anchor}"



    response = dashscope.Generation.call(
        model="qwen-plus",
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": user_msg
            },
        ],
        result_format="message",
    )

    # API失败
    if response.status_code != 200:
        raise RuntimeError(
            f"通义千问调用失败 | "
            f"状态码: {response.status_code} | "
            f"{response.message}"
        )

    raw_text = response.output.choices[0].message.content.strip()

    # 去除 ```json
    if raw_text.startswith("```"):
        lines = raw_text.splitlines()

        raw_text = "\n".join(
            line for line in lines
            if not line.startswith("```")
        ).strip()

    # JSON解析
    try:
        result = json.loads(raw_text)

    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"模型返回非 JSON 格式\n\n"
            f"原始返回：\n{raw_text}\n\n"
            f"错误：{e}"
        )

    # 检查字段
    required = {
        "style_anchor",
        "front_prompt",
        "back_prompt",
        "sleeve_prompt",
        "badge_prompt",
    }

    missing = required - result.keys()

    if missing:
        raise RuntimeError(
            f"返回 JSON 缺少字段：{missing}\n"
            f"原始返回：{raw_text}"
        )

    # ─────────────────────────────
    # 风格锚点拼接（核心）
    # ─────────────────────────────
    anchor = result["style_anchor"]

    for key in [
        "front_prompt",
        "back_prompt",
        "sleeve_prompt",
        "badge_prompt",
    ]:
        result[key] = f"{anchor}，{result[key]}"

    return result

