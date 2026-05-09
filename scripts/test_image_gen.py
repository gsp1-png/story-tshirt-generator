"""
测试模块 2：只生成"袖口"这一张图
袖口 prompt 最简单、尺寸最小（512x512），最省钱省时
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.image_gen import generate_image

# 用刚才模块1输出的 sleeve_prompt
SLEEVE_PROMPT = (
    "正方形小图：一枚悬浮的圆形徽记，内为极简线条构成的'空心人形'——"
    "仅由一道闭合的、微微起伏的单线勾勒，中心完全留白，"
    "线条末端自然晕散成两缕青灰气流，背景纯白"
)

print("只生成袖口一张，验证图像模块是否正常...\n")

try:
    path = generate_image(
        prompt=SLEEVE_PROMPT,
        position="sleeve",
        save_dir="outputs/test",
        filename="sleeve_test.png",
    )
    print(f"\n✅ 模块2测试通过，图片在：{path}")
    print("用文件管理器打开 outputs/test/ 文件夹查看图片")
except RuntimeError as e:
    print(f"\n❌ 出错：{e}")