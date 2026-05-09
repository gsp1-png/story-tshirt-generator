"""
app.py — 故事 T 恤设计生成器
运行：streamlit run app.py
"""

import os
import zipfile
import tempfile
import streamlit as st
from pathlib import Path
from PIL import Image

# ── 页面配置 ─────────────────────────────────────────────────────
st.set_page_config(
    page_title="故事 T 恤设计生成器",
    page_icon="👕",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── 样式 ─────────────────────────────────────────────────────────
st.markdown("""
<style>
html, body, [class*="css"] {
    font-family: "PingFang SC", "Microsoft YaHei", sans-serif;
}

.title-block {
    text-align: center;
    padding: 2rem 0 1rem;
}
.title-block h1 {
    font-size: 2rem;
    font-weight: 700;
    margin-bottom: 0.3rem;
}
.title-block p {
    color: #888;
    font-size: 0.95rem;
}

.step-badge {
    display: inline-block;
    background: #f0f0f0;
    border-radius: 12px;
    padding: 2px 10px;
    font-size: 0.75rem;
    color: #555;
    margin-bottom: 6px;
}

.section-divider {
    border: none;
    border-top: 1px solid #eee;
    margin: 1.5rem 0;
}
</style>
""", unsafe_allow_html=True)

# ── 标题 ─────────────────────────────────────────────────────────
st.markdown("""
<div class="title-block">
  <h1>👕 故事 T 恤设计生成器</h1>
  <p>输入故事 · 上传风格参考图 · 自动生成 4 版位设计 + T 恤效果</p>
</div>
""", unsafe_allow_html=True)

st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)


# ── Session State ───────────────────────────────────────────────
if "result" not in st.session_state:
    st.session_state.result = None


# ── 输入区 ───────────────────────────────────────────────────────
left, right = st.columns([3, 2], gap="large")

with left:
    st.markdown("### 📝 第 1 步：输入故事")

    story_text = st.text_area(
        label="story",
        label_visibility="collapsed",
        placeholder="请输入故事...",
        height=220,
    )

with right:
    st.markdown("### 🎨 第 2 步：上传风格图")

    ref_file = st.file_uploader(
        label="ref",
        label_visibility="collapsed",
        type=["png", "jpg", "jpeg", "webp"],
    )

    if ref_file:
        st.image(Image.open(ref_file), use_column_width=True)
    else:
        st.info("上传参考图")


# ── 生成按钮 ─────────────────────────────────────────────────────
st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

generate_btn = st.button(
    "✨ 开始生成",
    type="primary",
    use_container_width=True,
    disabled=(len(story_text.strip()) < 10 or ref_file is None),
)


# ── 生成流程 ─────────────────────────────────────────────────────
if generate_btn:

    st.session_state.result = None

    with tempfile.NamedTemporaryFile(
        suffix=Path(ref_file.name).suffix, delete=False
    ) as tmp:
        tmp.write(ref_file.getbuffer())
        ref_path = tmp.name

    save_dir = "outputs/current_run"
    Path(save_dir).mkdir(parents=True, exist_ok=True)

    progress = st.progress(0, text="生成中...")
    status = st.empty()

    try:
        status.info("🧠 分析故事...")

        from src.pipeline import run_pipeline
        result = run_pipeline(
            story_text=story_text,
            reference_image_path=ref_path,
            save_dir=save_dir,
        )

        progress.progress(60)

        status.info("👕 合成T恤效果...")

        from src.mockup import create_mockup

        front = "assets/tshirt_mockup.png"
        back = "assets/tshirt_back.png" if Path("assets/tshirt_back.png").exists() else front

        mockup = create_mockup(
            tshirt_path=front,
            image_paths=result["images"],
            output_path=f"{save_dir}/mockup.png",
            tshirt_back_path=back,
        )

        progress.progress(100)
        status.success("完成！")

        st.session_state.result = {
            "images": result["images"],
            "mockup": mockup,
            "story": story_text,
        }

    finally:
        os.unlink(ref_path)


# ── 结果展示 ─────────────────────────────────────────────────────
if st.session_state.result:

    res = st.session_state.result
    images = res["images"]
    mockup = res["mockup"]

    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
    st.markdown("## 🎨 4 版位设计图")

    LABELS = {
        "front": "前胸主图",
        "back": "后背",
        "sleeve": "袖口",
        "badge": "胸章",
    }

    cols = st.columns(4)

    for i, key in enumerate(["front", "back", "sleeve", "badge"]):

        with cols[i]:

            path = images.get(key)

            if path and Path(path).exists():

                st.image(path, use_column_width=True)

                # ✅ 只显示名字（无 prompt）
                st.markdown(f"**{LABELS[key]}**")

                # ✅ 单图下载（恢复）
                with open(path, "rb") as f:
                    st.download_button(
                        label=f"⬇ 下载 {LABELS[key]}",
                        data=f,
                        file_name=f"{key}.png",
                        mime="image/png",
                        key=f"dl_{key}",
                        use_container_width=True,
                    )

            else:
                st.warning("未生成")


    # ── Mockup ───────────────────────────────────────────────
    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
    st.markdown("## 👕 T 恤效果")

    c1, c2 = st.columns(2)

    with c1:
        st.image(mockup.get("front"), use_column_width=True, caption="正面")

    with c2:
        st.image(mockup.get("back"), use_column_width=True, caption="背面")


    # ── ZIP 下载 ─────────────────────────────────────────────
    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

    files = list(images.values()) + list(mockup.values())
    files = [f for f in files if f and Path(f).exists()]

    zip_path = tempfile.NamedTemporaryFile(delete=False, suffix=".zip").name

    with zipfile.ZipFile(zip_path, "w") as z:
        for f in files:
            z.write(f, Path(f).name)

    with open(zip_path, "rb") as f:
        st.download_button(
            "📦 下载全部",
            f,
            file_name="tshirt.zip",
            mime="application/zip",
            type="primary",
        )

    os.unlink(zip_path)


    # ── 故事回顾 ─────────────────────────────────────────────
    with st.expander("📖 故事"):
        st.text(res["story"])