from PIL import Image, ImageDraw, ImageFilter
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
        arr[0:s, W - s:W],
        arr[H - s:H, 0:s],
        arr[H - s:H, W - s:W],
    ]

    all_corners = np.concatenate([c.reshape(-1, 3) for c in corners])

    bg = np.median(all_corners, axis=0).astype(int)

    return tuple(bg)


# ─────────────────────────────────────────────────────────────
# 保留函数（现在不用）
# ─────────────────────────────────────────────────────────────

def soft_remove_bg(
    design: Image.Image,
    tshirt_color: tuple,
    design_bg: tuple = None,
    tolerance: int = 40
) -> Image.Image:

    return design.convert("RGBA")


def multiply_blend(
    base: Image.Image,
    overlay: Image.Image,
    opacity: float = 0.18
) -> Image.Image:

    return overlay


def displacement_warp(
    design: Image.Image,
    fabric_region: Image.Image,
    strength: float = 3.0
) -> Image.Image:

    return design


# ─────────────────────────────────────────────────────────────
# 前胸风格（高级海报风）
# ─────────────────────────────────────────────────────────────

def shape_front(design: Image.Image, width: int) -> Image.Image:
    """
    前胸：
    高清缩放 + 圆角海报风
    """

    w, h = design.size

    new_h = int(h * width / w)

    design = design.resize(
        (width, new_h),
        Image.LANCZOS
    )

    # 圆角遮罩
    radius = int(width * 0.04)

    mask = Image.new(
        "L",
        (width, new_h),
        0
    )

    draw = ImageDraw.Draw(mask)

    draw.rounded_rectangle(
        [0, 0, width, new_h],
        radius=radius,
        fill=255
    )

    # 轻微羽化
    mask = mask.filter(
        ImageFilter.GaussianBlur(radius=1.5)
    )

    design.putalpha(mask)

    return design


# ─────────────────────────────────────────────────────────────
# 后背风格（日系 editorial）
# ─────────────────────────────────────────────────────────────

def shape_back(design: Image.Image, width: int) -> Image.Image:
    """
    后背：
    竖版海报风格
    """

    w, h = design.size

    target_ratio = 1.28

    target_h = int(w * target_ratio)

    # 居中裁切
    if h >= target_h:

        top = (h - target_h) // 2

        design = design.crop(
            (0, top, w, top + target_h)
        )

    else:

        canvas = Image.new(
            "RGBA",
            (w, target_h),
            (0, 0, 0, 0)
        )

        canvas.paste(
            design,
            (0, (target_h - h) // 2)
        )

        design = canvas

    new_h = int(width * target_ratio)

    design = design.resize(
        (width, new_h),
        Image.LANCZOS
    )

    # 圆角
    radius = int(width * 0.035)

    mask = Image.new(
        "L",
        (width, new_h),
        0
    )

    draw = ImageDraw.Draw(mask)

    draw.rounded_rectangle(
        [0, 0, width, new_h],
        radius=radius,
        fill=255
    )

    # 羽化
    mask = mask.filter(
        ImageFilter.GaussianBlur(radius=1.5)
    )

    design.putalpha(mask)

    return design


# ─────────────────────────────────────────────────────────────
# 袖口（保持原逻辑）
# ─────────────────────────────────────────────────────────────

def shape_sleeve(
    design: Image.Image,
    width: int,
    angle: float = -40.0
) -> Image.Image:

    w, h = design.size

    canvas_w = width
    canvas_h = width * 2

    scale = min(canvas_w / w, canvas_h / h)

    fit_w = int(w * scale)
    fit_h = int(h * scale)

    design = design.resize(
        (fit_w, fit_h),
        Image.LANCZOS
    )

    canvas = Image.new(
        "RGBA",
        (canvas_w, canvas_h),
        (0, 0, 0, 0)
    )

    offset_x = (canvas_w - fit_w) // 2
    offset_y = (canvas_h - fit_h) // 2

    canvas.paste(
        design,
        (offset_x, offset_y),
        design
    )

    canvas = canvas.rotate(
        angle,
        resample=Image.BICUBIC,
        expand=True
    )

    return canvas


# ─────────────────────────────────────────────────────────────
# 胸章（保持原逻辑）
# ─────────────────────────────────────────────────────────────

def shape_badge(design: Image.Image, width: int) -> Image.Image:

    w, h = design.size

    side = min(w, h)

    left = (w - side) // 2
    top = (h - side) // 2

    design = design.crop(
        (left, top, left + side, top + side)
    )

    design = design.resize(
        (width, width),
        Image.LANCZOS
    )

    mask = Image.new("L", (width, width), 0)

    draw = ImageDraw.Draw(mask)

    draw.ellipse(
        [0, 0, width - 1, width - 1],
        fill=255
    )

    design.putalpha(mask)

    return design


SHAPE_FUNCS = {
    "front": shape_front,
    "back": shape_back,
    "sleeve": shape_sleeve,
    "badge": shape_badge,
}


# ─────────────────────────────────────────────────────────────
# 高清直贴
# 不做：
# - 去背
# - 正片叠底
# - 模糊
# - 褶皱
# ─────────────────────────────────────────────────────────────

def paste_design(
    tshirt: Image.Image,
    design_path: str,
    center_x: int,
    center_y: int,
    width: int,
    tshirt_color: tuple,
    position_key: str = "front"
):

    design = Image.open(design_path).convert("RGBA")

    print(f"  高清贴图模式：{design_path}")

    # 只做版型处理
    shape_fn = SHAPE_FUNCS.get(
        position_key,
        shape_front
    )

    design = shape_fn(design, width)

    w, h = design.size

    x = center_x - w // 2
    y = center_y - h // 2

    # 直接高清贴图
    tshirt.paste(
        design,
        (x, y),
        design
    )


# ─────────────────────────────────────────────────────────────
# 主函数
# ─────────────────────────────────────────────────────────────

def create_mockup(
    tshirt_path: str,
    image_paths: dict,
    output_path: str,
    positions: dict = None,
    tshirt_back_path: str = None,
):

    # ─────────────────────────────────────────
    # 正面
    # ─────────────────────────────────────────

    front_tshirt = Image.open(
        tshirt_path
    ).convert("RGBA")

    W, H = front_tshirt.size

    tshirt_color = detect_tshirt_color(
        front_tshirt
    )

    print(f"🎨 检测到 T 恤底色：RGB{tshirt_color}")

    front_positions = positions or {

        "front": dict(
            cx=int(W * 0.50),
            cy=int(H * 0.55),
            w=int(W * 0.30)
        ),

        "sleeve": dict(
            cx=int(W * 0.25),
            cy=int(H * 0.35),
            w=int(W * 0.06)
        ),

        "badge": dict(
            cx=int(W * 0.60),
            cy=int(H * 0.30),
            w=int(W * 0.08)
        ),
    }

    for key in ("front", "sleeve", "badge"):

        if key not in image_paths:
            continue

        if key not in front_positions:
            print(f"⚠️  版位 '{key}' 没有坐标配置")
            continue

        c = front_positions[key]

        paste_design(
            front_tshirt,
            image_paths[key],
            c["cx"],
            c["cy"],
            c["w"],
            tshirt_color,
            position_key=key,
        )

        print(f"✅ 正面版位已贴：{key}")

    out_dir = Path(output_path).parent

    out_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    front_out = str(
        out_dir / "mockup_front.png"
    )

    front_tshirt.save(front_out)

    print(f"🎉 正面 mockup 已保存：{front_out}")

    # ─────────────────────────────────────────
    # 背面
    # ─────────────────────────────────────────

    back_template = tshirt_back_path or tshirt_path

    back_tshirt = Image.open(
        back_template
    ).convert("RGBA")

    W2, H2 = back_tshirt.size

    tshirt_color2 = detect_tshirt_color(
        back_tshirt
    )

    back_positions = {

        "back": dict(
            cx=int(W2 * 0.50),
            cy=int(H2 * 0.52),
            w=int(W2 * 0.28)
        ),
    }

    if "back" in image_paths:

        c = back_positions["back"]

        paste_design(
            back_tshirt,
            image_paths["back"],
            c["cx"],
            c["cy"],
            c["w"],
            tshirt_color2,
            position_key="back",
        )

        print(f"✅ 背面版位已贴：back")

    back_out = str(
        out_dir / "mockup_back.png"
    )

    back_tshirt.save(back_out)

    print(f"🎉 背面 mockup 已保存：{back_out}")

    return {
        "front": front_out,
        "back": back_out,
    }