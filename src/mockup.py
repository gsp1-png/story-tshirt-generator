from PIL import Image
from pathlib import Path
import numpy as np


def detect_tshirt_color(tshirt: Image.Image) -> tuple:
    arr = np.array(tshirt.convert("RGBA"))
    H, W = arr.shape[:2]
    cx1, cx2 = int(W * 0.35), int(W * 0.65)
    cy1, cy2 = int(H * 0.40), int(H * 0.70)
    center = arr[cy1:cy2, cx1:cx2]
    mask = center[:, :, 3] > 200
    if mask.sum() == 0:
        return (255, 255, 255)
    pixels = center[mask][:, :3]
    avg = pixels.mean(axis=0).astype(int)
    return tuple(avg)


def detect_design_bg_color(design: Image.Image, sample_size: int = 20) -> tuple:
    arr = np.array(design.convert("RGB"))
    H, W = arr.shape[:2]
    s = sample_size
    corners = [
        arr[0:s, 0:s],
        arr[0:s, W-s:W],
        arr[H-s:H, 0:s],
        arr[H-s:H, W-s:W],
    ]
    all_corners = np.concatenate([c.reshape(-1, 3) for c in corners])
    bg = np.median(all_corners, axis=0).astype(int)
    return tuple(bg)


def soft_remove_bg(design: Image.Image, tshirt_color: tuple,
                   design_bg: tuple = None,
                   tolerance: int = 60) -> Image.Image:
    design = design.convert("RGBA")
    arr = np.array(design).astype(np.float32)
    if design_bg is None:
        design_bg = detect_design_bg_color(design)
    print(f"  🎯 识别到设计图背景色：RGB{tuple(int(x) for x in design_bg)}")
    bg = np.array(design_bg, dtype=np.float32)
    diff = arr[:, :, :3] - bg
    distance = np.sqrt(np.sum(diff ** 2, axis=2))
    new_alpha = np.clip(
        (distance - tolerance) / tolerance * 255,
        0, 255
    )
    arr[:, :, 3] = np.minimum(arr[:, :, 3], new_alpha)
    blend_ratio = 1 - (new_alpha / 255)
    blend_ratio = blend_ratio[:, :, np.newaxis]
    tshirt_arr = np.array(tshirt_color, dtype=np.float32)
    arr[:, :, :3] = (
        arr[:, :, :3] * (1 - blend_ratio * 0.4)
        + tshirt_arr * blend_ratio * 0.4
    )
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")


def paste_design(tshirt: Image.Image, design_path: str,
                 center_x: int, center_y: int, width: int,
                 tshirt_color: tuple):
    design = Image.open(design_path).convert("RGBA")
    print(f"  处理 {design_path}")
    design = soft_remove_bg(design, tshirt_color)
    w, h = design.size
    new_h = int(h * width / w)
    design = design.resize((width, new_h), Image.LANCZOS)
    x = center_x - width // 2
    y = center_y - new_h // 2
    tshirt.paste(design, (x, y), design)


def create_mockup(
    tshirt_path: str,
    image_paths: dict,
    output_path: str,
    positions: dict = None,
    tshirt_back_path: str = None,    # ← 新增：背面模板，不传就复用正面模板
):
    """
    生成正面和背面两张 mockup。

    正面贴：front、sleeve、badge
    背面贴：back

    返回：
        {
            "front": "mockup_front.png 的路径",
            "back":  "mockup_back.png  的路径",
        }
    原来直接用 output_path 的地方，改成取 result["front"] 或 result["back"]。
    """

    # ── 正面 ─────────────────────────────────────────────────────
    front_tshirt = Image.open(tshirt_path).convert("RGBA")
    W, H = front_tshirt.size
    tshirt_color = detect_tshirt_color(front_tshirt)
    print(f"🎨 检测到 T 恤底色：RGB{tshirt_color}")

    front_positions = positions or {
        "front":  dict(cx=int(W * 0.50), cy=int(H * 0.51), w=int(W * 0.30)),
        "sleeve": dict(cx=int(W * 0.25), cy=int(H * 0.35), w=int(W * 0.08)),
        "badge":  dict(cx=int(W * 0.60), cy=int(H * 0.30), w=int(W * 0.08)),
    }

    for key in ("front", "sleeve", "badge"):
        if key not in image_paths:
            continue
        if key not in front_positions:
            print(f"⚠️  版位 '{key}' 没有坐标配置，跳过")
            continue
        c = front_positions[key]
        paste_design(front_tshirt, image_paths[key], c["cx"], c["cy"], c["w"], tshirt_color)
        print(f"✅ 正面版位已贴：{key}")

    # 正面输出路径：把 output_path 的文件名改成 mockup_front.png
    out_dir  = Path(output_path).parent
    out_dir.mkdir(parents=True, exist_ok=True)
    front_out = str(out_dir / "mockup_front.png")
    front_tshirt.save(front_out)
    print(f"🎉 正面 mockup 已保存：{front_out}")

    # ── 背面 ─────────────────────────────────────────────────────
    back_template = tshirt_back_path or tshirt_path   # 没有背面模板就用正面顶替
    back_tshirt   = Image.open(back_template).convert("RGBA")
    W2, H2        = back_tshirt.size
    tshirt_color2 = detect_tshirt_color(back_tshirt)

    back_positions = {
        "back": dict(cx=int(W2 * 0.50), cy=int(H2 * 0.48), w=int(W2 * 0.32)),
    }

    if "back" in image_paths:
        c = back_positions["back"]
        paste_design(back_tshirt, image_paths["back"], c["cx"], c["cy"], c["w"], tshirt_color2)
        print(f"✅ 背面版位已贴：back")

    back_out = str(out_dir / "mockup_back.png")
    back_tshirt.save(back_out)
    print(f"🎉 背面 mockup 已保存：{back_out}")

    return {"front": front_out, "back": back_out}