
import os
import time
import base64
import requests

from pathlib import Path
from dotenv import load_dotenv

import dashscope
from dashscope import ImageSynthesis

load_dotenv()

dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")


SIZE_MAP = {
    "front":  "1280*720",
    "back":   "1024*1024",
    "sleeve": "512*512",
    "badge":  "512*512",
}


def _load_image_base64(
    image_path: str,
    max_size: int = 256
) -> str:
    """
    加载参考图
    压缩后转 Data URI
    """

    from PIL import Image
    import io

    img = Image.open(image_path)

    # 等比缩小
    img.thumbnail(
        (max_size, max_size),
        Image.LANCZOS
    )

    buf = io.BytesIO()

    img.save(buf, format="PNG")

    base64_str = base64.b64encode(
        buf.getvalue()
    ).decode("utf-8")

    print("参考图 base64 长度:", len(base64_str))

    return f"data:image/png;base64,{base64_str}"


def generate_image(
    prompt: str,
    position: str,
    save_dir: str = "outputs",
    filename: str = None,
    style_image_path: str = None,   # 用户上传参考图
) -> str:

    size = SIZE_MAP.get(position, "1024*1024")

    Path(save_dir).mkdir(
        parents=True,
        exist_ok=True
    )

    if filename is None:
        filename = f"{position}_{int(time.time())}.png"

    save_path = Path(save_dir) / filename

    # ─────────────────────────────
    # 使用参考图约束风格
    # ─────────────────────────────
    if style_image_path:

        print(
            f"  ⏳ 生成 [{position}] "
            f"（参考用户风格图）..."
        )

        response = ImageSynthesis.call(
            model="wanx2.1-t2i-turbo",

            prompt=prompt,

            n=1,

            size=size,

            ref_image=_load_image_base64(
                style_image_path
            ),

            ref_strength=0.5,

            ref_mode="style",
        )

    # ─────────────────────────────
    # 无参考图
    # ─────────────────────────────
    else:

        print(
            f"  ⏳ 生成 [{position}] ..."
        )

        response = ImageSynthesis.call(
            model="wanx2.1-t2i-turbo",

            prompt=prompt,

            n=1,

            size=size,
        )

    # API失败
    if response.status_code != 200:

        raise RuntimeError(
            f"图像生成失败 | "
            f"版位: {position} | "
            f"状态码: {response.status_code} | "
            f"{response.message}"
        )

    # 获取图片URL
    img_url = response.output.results[0].url

    # 下载图片
    img_data = requests.get(
        img_url,
        timeout=60
    ).content

    save_path.write_bytes(img_data)

    print(f"  ✅ 已保存：{save_path}")

    return str(save_path)
