
from src.pipeline import run_pipeline

STORY = """
少年在雪夜背剑远行，
乌鸦掠过冰封河面，
寺庙钟声回荡山谷。
"""

result = run_pipeline(

    story_text=STORY,

    # 这里设置你的风格图路径
    reference_image_path="assets/style.png",

    save_dir="outputs/pipeline_test",
)

print(result)

