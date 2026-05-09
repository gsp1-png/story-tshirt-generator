"""
scripts/calibrate_mockup.py
运行后会生成 outputs/calibrate.png
用肉眼看圆点是否落在正确位置，调整下面的比例数字
"""
from PIL import Image, ImageDraw
from pathlib import Path

TSHIRT_PATH = "assets/tshirt_mockup.png"

# ── 在这里调整比例（0~1 表示相对图片宽/高的百分比）──────────
# 格式：(水平位置, 垂直位置, 圆点大小)
SPOTS = {
    "前胸 front":  (0.50, 0.51, 40),   # 胸口正中
    "胸章 badge":  (0.60, 0.30, 20),   # 左胸口袋位
    "左袖 sleeve": (0.25, 0.35, 15),   # 左袖中间
}

img = Image.open(TSHIRT_PATH).convert("RGBA")
W, H = img.size
print(f"T 恤模板尺寸：{W} x {H}")

draw = ImageDraw.Draw(img)
COLORS = {"前胸 front": "red", "胸章 badge": "blue", "左袖 sleeve": "green"}

for name, (rx, ry, r) in SPOTS.items():
    cx, cy = int(W * rx), int(H * ry)
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=COLORS[name], outline="black")
    draw.text((cx+r+5, cy-10), name, fill=COLORS[name])
    print(f"{name}: 像素坐标 ({cx}, {cy})")

out = "outputs/calibrate.png"
Path(out).parent.mkdir(parents=True, exist_ok=True)
img.save(out)
print(f"\n✅ 校准图已保存：{out}")
print("用 VS Code 打开这张图，看圆点是否在正确位置")
print("不对就修改 SPOTS 里的比例数字，重新跑")