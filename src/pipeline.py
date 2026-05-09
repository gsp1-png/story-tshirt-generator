
"""
主流程：故事 → 4 张图
"""

from src.style_extractor import extract_style
import json
import time

from src.story_parser import parse_story
from src.image_gen import generate_image


def run_pipeline(
    story_text: str,
    reference_image_path: str,
    save_dir: str = "outputs",
):
    """
    完整流程：故事文本 → 4 张本地图片路径
    """

    # ─────────────────────────────
    # Step 1：故事拆解
    # ─────────────────────────────
    print("【Step 1】拆解故事...")
    print("【Step 1】分析参考图风格...")

    style_anchor = extract_style(
        reference_image_path
    )

    print("  风格锚点：", style_anchor)
    print("  ✅ 风格分析完成\n")
    prompts = parse_story(
        story_text,
        style_anchor,
    )

    print("  ✅ 拆解完成\n")

    # ─────────────────────────────
    # Step 2：生成四张图
    # 全部使用用户参考图约束风格
    # ─────────────────────────────
    print("【Step 2】生成四张版位图...")

    timestamp = int(time.time())

    image_paths = {}

    for position in [
        "front",
        "back",
        "sleeve",
        "badge",
    ]:

        print(f"\n正在生成：{position}")

        path = generate_image(

            prompt=prompts[f"{position}_prompt"],

            position=position,

            save_dir=save_dir,

            filename=f"{position}_{timestamp}.png",

            # 用户上传参考图
            style_image_path=reference_image_path,
        )

        image_paths[position] = path

        # 避免请求过快
        time.sleep(5)

    print("\n✅ 全部完成！\n")
    prompts_clean = {k.replace("_prompt", ""): v for k, v in prompts.items()}
    return {
        "prompts": prompts,
        "images": image_paths,
    }
