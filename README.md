# 故事- T 恤设计生成器

输入一段故事文本，上传一张风格参考图，自动生成 4 个版位的 T 恤设计图 + 正背面上身效果（Mockup）。

---

## 效果说明

| 版位 | 生成尺 | 设计定位 |
|---|---|---|
| **前胸 front** | 1280×720 | 主视觉，承载故事核心意象 |
| **后背 back** | 1024×1024 | 叙事延伸，场景展开或加入文字 |
| **袖口 sleeve** | 512×512 | 极简符号，一个图标即可 |
| **胸章 badge** | 512×512 | 章印感，浓缩符号 + 短词 |

---

## 系统架构

```
用户输入：故事文本 + 参考图
            │
            ▼
  style_extractor.py
  模型：qwen-vl-max（多模态视觉）
  → 分析参考图，输出风格锚点（40字内关键词）
            │
            ▼
  story_parser.py
  模型：qwen-plus（文本LLM）
  → 把故事拆解为 4 版位 JSON Prompt
  → 每个 Prompt 自动拼接风格锚点
            │
            ▼
  image_gen.py
  模型：wanx2.1-t2i-turbo（通义万相）
  ref_mode="style" 用参考图约束风格
  → 4 张 PNG 保存到 outputs/
            │
            ▼
  mockup.py
  工具：Pillow + Numpy
  → 自动识别 T 恤底色
  → 渐变融合贴图（去白边）
  → 输出 mockup_front.png + mockup_back.png
            │
            ▼
  app.py（Streamlit）
  → 输入 / 生成 / 展示 / 下载
```

**所有 AI 能力均走阿里云 DashScope，只需要一个 API Key。**

---

## **项目结构**

```
story-tshirt/
├── app.py                    # Streamlit Web 主入口
├── requirements.txt              # Key 配置模板（不含真实 Key）
├── .gitignore
├── src/
│   ├── style_extractor.py    # 参考图 → 风格锚点（qwen-vl-max）
│   ├── story_parser.py       # 故事 → 4 版位 Prompt（qwen-plus）
│   ├── image_gen.py          # Prompt → 图片（wanx2.1-t2i-turbo）
│   ├── mockup.py             # 图片 → T恤效果图（Pillow + Numpy）
│   └── pipeline.py           # 串联以上四个模块
├── assets/   
│	├──style1.png             #四种不同的测试用参考图（用户也可自己上传）
│	├──style2.png
│	├──style3.png
│	├──style4.png
│   ├── tshirt_mockup.png     #正面T恤模板
│   └── tshirt_back.png       # 背面T恤模板
├── outputs/                  # 自动生成，存放每次运行结果
└── scripts/
    ├── test_mockup.py        # 单独测试 Mockup 合成
    └── calibrate_mockup.py   # 版位坐标校准工具
```

## 风格一致性方案

4 张图保持风格统一是本项目的核心技术难点，用三层保险：

| 层                    | 代码位置                                                   | 作用               |
| --------------------- | ---------------------------------------------------------- | ------------------ |
| 风格锚点拼接          | `story_parser.py` 最后把 `style_anchor` 拼到每个 Prompt 前 | 语义层约束         |
| 参考图 style 模式     | `image_gen.py` 中 `ref_mode="style", ref_strength=0.5`     | 视觉层约束色调笔触 |
| 统一模型 + 统一参考图 | 所有版位调同一个模型、传同一张参考图                       | 减少随机性来源     |

## 安装

### 第一步：装 Python 3.12

去 https://www.python.org/downloads/ 下载 Python 3.12 安装包。

⚠️ 安装时必须勾选 **"Add python.exe to PATH"**，否则后续所有命令都找不到 python。

装完打开 VS Code，按 `Ctrl + `` 打开终端，确认：

```powershell
python --version
# 应显示 Python 3.12.x
```

### 第二步：创建虚拟环境并安装依赖

```powershell
# 进入项目目录（改成你自己的路径）
cd D:\projects\story-tshirt

# 创建虚拟环境
python -m venv .venv

# 激活（每次新开终端都要执行这行）
.venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

如果激活时报 `running scripts is disabled`，先执行：

```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
# 输入 Y 确认
```

### 第三步：配置 API Key

用 VS Code 创建 `.env`，填入：

```
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
```

**获取方式：**

1. 访问 https://dashscope.console.aliyun.com/，用支付宝扫码登录
2. 完成个人实名认证
3. 进入「模型广场」，依次开通：
   - **通义千问 qwen-plus**（故事拆解）
   - **qwen-vl-max**（参考图风格分析）
   - **通义万相 wanx2.1-t2i-turbo**（图像生成）
4. 左侧菜单 → **API Key 管理** → 新建 → 复制保存

---

## 运行

```powershell
# 确认虚拟环境已激活（提示符最左边显示 (.venv)）
streamlit run app.py
```

浏览器自动打开 `http://localhost:8501`。

---

## 使用流程

1. 在左侧文本框输入故事（诗词、神话、场景描述均可，50–500 字最佳）
2. 上传一张风格参考图（水墨、插画、版画效果最好，避免用普通照片）
3. 点击「开始生成」，等待 1–3 分钟
4. 查看 4 张设计图 + 正背面 T 恤上身效果
5. 单张下载或一键打包 ZIP

---

## 常见问题

**Q: `ModuleNotFoundError: No module named 'dashscope'`**  
A: 虚拟环境未激活。先执行 `.venv\Scripts\activate`，再运行 `pip install -r requirements.txt`。

**Q: 4 张图风格差异明显**  
A: 参考图风格越鲜明，一致性越好。推荐用有明确艺术风格的图（水墨、版画、插画），避免普通照片。可适当调高 `ref_strength`（最大 1.0）。

**Q: Mockup 贴图位置跑偏**  
A: T 恤模板换了之后需要重新校准坐标。运行 `python scripts/calibrate_mockup.py`，按脚本提示调整比例，3 轮以内能对准。

**Q: 实名认证一直在审核**  
A: 一般 5–30 分钟，最长一小时。等审核期间可以先把代码环境搭好、先不跑需要 API 的部分。
