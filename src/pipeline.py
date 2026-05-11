"""
主流程：故事 → 4 张图
"""

from src.style_extractor import extract_style
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

    生成顺序：front → back → sleeve → badge
    - front / back：用用户参考图，ref_mode=refonly，约束整体风格
    - sleeve：在 front 生成图上 repaint，直接继承人物形象
    - badge ：在 back  生成图上 repaint，直接继承人物形象
    """

    # ─────────────────────────────
    # Step 1：分析参考图风格 + 拆解故事
    # ─────────────────────────────
    print("【Step 1】分析参考图风格...")
    style_anchor = extract_style(reference_image_path)
    print("  风格锚点：", style_anchor)
    print("  ✅ 风格分析完成\n")

    print("【Step 1】拆解故事...")
    prompts = parse_story(story_text, style_anchor)
    print("  ✅ 拆解完成\n")

    print("\n===== 生成提示词 =====")
    print(f"风格锚点：{prompts['style_anchor']}")
    print(f"前胸：{prompts['front_prompt']}")
    print(f"后背：{prompts['back_prompt']}")
    print(f"袖口：{prompts['sleeve_prompt']}")
    print(f"胸章：{prompts['badge_prompt']}")
    print("=====================\n")

    # ─────────────────────────────
    # Step 2：生成四张图
    #
    # 分组逻辑：
    #   组A（同一故事）：front + sleeve
    #   组B（同一故事）：back  + badge
    #
    # front / back：用用户参考图，refonly，ref_strength=0.5（约束风格）
    # sleeve：在 front 生成图上 repaint，ref_strength=0.6（继承人物形象）
    # badge ：在 back  生成图上 repaint，ref_strength=0.6（继承人物形象）
    # ─────────────────────────────
    print("【Step 2】生成四张版位图...")

    timestamp = int(time.time())
    image_paths = {}

    # ── 组A 第一张：front（用用户参考图，约束整体风格）──
    print("\n正在生成：front")
    front_path = generate_image(
        prompt=prompts["front_prompt"],
        position="front",
        save_dir=save_dir,
        filename=f"front_{timestamp}.png",
        style_image_path=reference_image_path,
        ref_mode="refonly",
        ref_strength=0.5,
    )
    image_paths["front"] = front_path
    time.sleep(5)

    # ── 组B 第一张：back（用用户参考图，约束整体风格）──
    print("\n正在生成：back")
    back_path = generate_image(
        prompt=prompts["back_prompt"],
        position="back",
        save_dir=save_dir,
        filename=f"back_{timestamp}.png",
        style_image_path=reference_image_path,
        ref_mode="refonly",
        ref_strength=0.5,
    )
    image_paths["back"] = back_path
    time.sleep(5)

    # ── 组A 第二张：sleeve（在 front 生成图上重绘，继承人物形象）──
    print("\n正在生成：sleeve（在 front 生成图上重绘）")
    sleeve_path = generate_image(
        prompt=prompts["sleeve_prompt"],
        position="sleeve",
        save_dir=save_dir,
        filename=f"sleeve_{timestamp}.png",
        style_image_path=front_path,
        ref_mode="repaint",      # 在参考图上重绘，直接继承人物形象
        ref_strength=0.6,        # 0.6：保留人物，允许构图变化
    )
    image_paths["sleeve"] = sleeve_path
    time.sleep(5)

    # ── 组B 第二张：badge（在 back 生成图上重绘，继承人物形象）──
    print("\n正在生成：badge（在 back 生成图上重绘）")
    badge_path = generate_image(
        prompt=prompts["badge_prompt"],
        position="badge",
        save_dir=save_dir,
        filename=f"badge_{timestamp}.png",
        style_image_path=back_path,
        ref_mode="repaint",      # 在参考图上重绘，直接继承人物形象
        ref_strength=0.6,        # 0.6：保留人物，允许构图变化
    )
    image_paths["badge"] = badge_path

    print("\n✅ 全部完成！\n")

    return {
        "prompts": prompts,
        "images": image_paths,
    }