"""
scripts/test_mockup.py
"""

from src.pipeline import run_pipeline
from src.mockup import create_mockup


STORY = """
两只老虎两只老虎跑得快跑得快一只没有耳朵一只没有尾巴真奇怪真奇怪
"""


# ==========================================
# Step 1：生成四张设计图
# ==========================================

result = run_pipeline(
    story_text=STORY,
    reference_image_path="assets/style.png",
    save_dir="outputs/pipeline_test",
)

print("pipeline 返回结果：", result)  # 先打印出来，确认 images 的格式


# ==========================================
# Step 2：读取四张图路径
# ==========================================

# result["images"] 应该长这样：
# {
#     "front":  "outputs/pipeline_test/front.png",
#     "back":   "outputs/pipeline_test/back.png",
#     "sleeve": "outputs/pipeline_test/sleeve.png",
#     "badge":  "outputs/pipeline_test/badge.png",
# }
image_paths = result["images"]


# ==========================================
# Step 3：合成 Mockup
# ==========================================

result = create_mockup(
    tshirt_path="assets/tshirt_mockup.png",
    image_paths=image_paths,
    output_path="outputs/mockup/final_mockup.png",
    tshirt_back_path="assets/tshirt_back.png",  
)
print("正面：", result["front"])
print("背面：", result["back"])
