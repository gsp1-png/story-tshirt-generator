"""
故事拆解模块：将故事文本拆解为 4 个版位的图像生成提示词
核心改动：强制所有出场人物（含配角）用完整外貌档案等量呈现
"""

import json
import re
import dashscope
import os
from dotenv import load_dotenv

load_dotenv()
dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")


SYSTEM_PROMPT = """
你是一位专注于服装印花设计的视觉创意总监。

任务分四步，严格按顺序执行。

【第一步：原文动作句摘录】
逐句扫描故事原文，把所有包含"具体动作"的句子原样照抄列出来。
具体动作 = 谁做了什么、谁说了什么、谁走到哪里、谁的表情怎么样。
模糊心理描述（"心情不好""觉得自卑"）不算具体动作，不要选。

【第二步：逐人建立完整档案】
扫描故事原文，把每一个出现过的人物全部找出来——
不只是主角，所有有名字、有身份、有动作、被提到的人都要建档。
配角（父亲、路人、同学等）也必须建档，不允许遗漏。

每个人物档案必须包括：
- 角色身份（主角/配角及其在故事中的关系，如"儿子""父亲""路人"）
- 性别 + 大致年龄
- 发型 + 发色（如"黑色短碎发""花白中长卷发"）
- 上衣 + 颜色 + 款式
- 下装 + 颜色 + 款式
- 体型 + 身高
- 标志性配饰（眼镜/书包/手提袋等，原文未提到则写"无"）

同一人物的档案在不同版位中必须逐字一致，禁止在不同版位里描述同一人物时外貌出现差异。

【第三步：版位分组与依据句选定】
front + sleeve 一组（同一故事），back + badge 一组（同一故事）。
如果只有一个故事，4 个版位按时间顺序（起因→发展→高潮→结尾）分配给同一个故事。
如果有多个故事，从中选两个，各占一组。

为每个版位从第一步的原文动作句中选定一句作为"依据句"，
四个版位的依据句来自不同时刻，不能重复。

为每个版位列出"出场人物清单"：
该版位的依据句里涉及到的所有人物，主角配角都要列。
依据句里如果同时出现"父亲"和"儿子"两个人，出场人物清单就必须包含两个人。

【第四步：扩写为长 prompt——多人场景必须每人完整呈现】

每个版位 prompt 必须按以下固定结构扩写，长度不少于 150 字：

  [风格锚点] +
  [出场人物清单中每一个人的完整档案，人物之间用"和""与"等连接，
   不允许把配角降级为"身后那位...""远处的..."这种附属修饰] +
  [谓语：依据句中的具体动作，每个出场人物都要有自己的动作描述] +
  [对象/朝向：动作针对的人或物] +
  [场景：在哪里、周围环境] +
  [细节：每个人物的手在做什么、脚在做什么、目光朝向、表情] +
  [构图：景别、视角、版位特征]

【多人场景的硬性约束】
1. 出场人物清单里有几个人，prompt 里就必须有几套完整的外貌描述
2. 严禁把配角写成"身后那位X的中年男人"这种附属化表述，
   配角的发型、服装、体型必须和主角等量呈现
3. 严禁在多人场景里只描述一个人的动作，
   每个出场人物都要有自己的可视化动作描述
4. 故事里同时出现的两个人，不允许其中一个被虚化、剪影化、模糊化处理

严禁出现的表述：
  - "因…而…""似乎""仿佛""若有所思"（心理化/模糊状态，生图模型无法画）
  - "身后的父亲""远处的妈妈"（配角附属化）
  - 故事原文未提及的人物、物品或场景

正反对比示例（故事：儿子嫌爸爸白头发，放学时假装不认识）：

✗ 错误："黑色短发、穿蓝白校服、瘦小的少年快步侧身绕到马路另一侧，
       低头快走，刻意不看身后那位穿灰色夹克、满头银白短发的中年父亲"
  问题：父亲被压成定语，是"被绕开的对象"，没有自己的动作和镜头分量。

✓ 正确："[风格锚点]，黑色短碎发、穿藏蓝校服外套配白色T恤、背深蓝双肩书包、
       身材瘦小的小学男生，在校门口右转绕到梧桐树后，低头加快步伐，
       右手紧攥书包带，左手抬起遮在右脸侧，目光朝地面；
       同一画面里，满头银白短发、穿灰色旧夹克外套配深色长裤、
       手提一个洗得发白的旧布袋、身材中等的中年男人，
       站在校门正前方人行道上，微微踮脚向校门内张望，
       右手举起准备招手，脸上是温和的笑容；
       两人相距约五米，男生背对父亲，父亲尚未察觉儿子已经绕开，
       校门口梧桐树影斑驳，远处几个学生背影模糊；横版主视觉构图，双主体并列"
  要点：儿子和父亲都有完整外貌档案、都有具体动作、都在画面里占据视觉位置。

输出格式（严格 JSON，不允许任何额外内容，不允许包含 Markdown 代码块标记）：

{
  "style_anchor": "覆盖色彩、笔触、构图、光影、材质、整体定语6个维度的详细描述",
  "story1_characters": [
    {"role": "角色身份", "appearance": "完整外貌档案逐条描述"},
    {"role": "角色身份", "appearance": "完整外貌档案逐条描述"}
  ],
  "story2_characters": [
    {"role": "角色身份", "appearance": "完整外貌档案逐条描述"}
  ],
  "front_source": "依据句原文照抄",
  "front_cast": ["该版位出场的所有人物角色身份"],
  "front_prompt": "按第四步结构扩写的长描述，不少于150字",
  "back_source": "依据句原文照抄",
  "back_cast": ["该版位出场的所有人物角色身份"],
  "back_prompt": "按第四步结构扩写的长描述，不少于150字",
  "sleeve_source": "依据句原文照抄",
  "sleeve_cast": ["该版位出场的所有人物角色身份"],
  "sleeve_prompt": "按第四步结构扩写的长描述，不少于150字",
  "badge_source": "依据句原文照抄",
  "badge_cast": ["该版位出场的所有人物角色身份"],
  "badge_prompt": "按第四步结构扩写的长描述，不少于150字"
}
"""


def parse_story(
    story_text: str,
    style_anchor: str = None,
) -> dict:
    """
    将故事文本拆解为 4 个版位的图像生成提示词。

    Args:
        story_text:   故事原文
        style_anchor: 风格锚点（来自 style_extractor，可选）

    Returns:
        包含 front_prompt / back_prompt / sleeve_prompt / badge_prompt 等字段的 dict
    """

    user_msg = f"""故事原文：
{story_text}

强制要求：
1. 故事里出现的所有人物必须全部建档，主角配角一视同仁；
   父亲、路人、同学等配角不许跳过，每个人都要有完整的外貌档案。
2. front 和 sleeve 必须写同一个故事，back 和 badge 必须写同一个故事。
3. 每个版位先写 cast 列出出场所有人物，prompt 里必须按 cast 数量写出对应数量的完整外貌描述。
4. 严禁把配角写成"身后那位...""远处的..."这类附属修饰；
   配角的发型、服装、体型必须和主角等量呈现，每个人都有自己的动作。
5. 多人场景里每个人都要有自己的具体动作描述，不允许只描述一个人、其他人虚化。
6. 每个 prompt 的动作描述必须来自 source 字段的原文句子，不允许概括或抽象化。
7. 每个 prompt 至少 150 字，把所有出场人物的外貌、动作细节、场景环境都写清楚。
8. 严禁出现"因…而""似乎""仿佛"等心理化表述。

把 prompt 当作给画师的工单：画里有几个人就要写几套档案，
每个人在哪里、做什么、手脚目光朝向，全部交代清楚。"""

    if style_anchor:
        user_msg += f"\n\n参考图风格：{style_anchor}"

    from dashscope import Generation

    response = Generation.call(
        model="qwen3-max",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_msg},
        ],
        result_format="message",
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"故事拆解 API 失败 | "
            f"状态码: {response.status_code} | "
            f"{response.message}"
        )

    raw = response.output.choices[0].message.content.strip()

    # 去掉可能包裹的 Markdown 代码块标记
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$",          "", raw)
    raw = raw.strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"JSON 解析失败：{e}\n原始返回：\n{raw}"
        )

    # ── 必需字段校验（缺失直接报错）──────────────────────
    required_fields = {
        "style_anchor",
        "story1_characters",
        "front_prompt",
        "back_prompt",
        "sleeve_prompt",
        "badge_prompt",
    }
    missing = required_fields - set(result.keys())
    if missing:
        raise RuntimeError(
            f"返回 JSON 缺少字段：{missing}\n原始返回：\n{raw}"
        )

    # ── 可选字段兜底（缺失给默认值，不崩溃）────────────────
    result.setdefault("story2_characters", [])
    for pos in ["front", "back", "sleeve", "badge"]:
        result.setdefault(f"{pos}_source", "")
        result.setdefault(f"{pos}_cast",   [])

    # ── 打印拆解结果，方便调试 ─────────────────────────────
    print("\n===== 故事拆解结果 =====")
    print(f"风格锚点：{result['style_anchor']}\n")

    print("── 故事1 人物档案 ──")
    for char in result.get("story1_characters", []):
        print(f"  [{char.get('role','')}] {char.get('appearance','')}")

    if result.get("story2_characters"):
        print("\n── 故事2 人物档案 ──")
        for char in result["story2_characters"]:
            print(f"  [{char.get('role','')}] {char.get('appearance','')}")

    print()
    for pos in ["front", "back", "sleeve", "badge"]:
        pos_name = {"front": "前胸", "back": "后背",
                    "sleeve": "袖口", "badge": "胸章"}[pos]
        print(f"── {pos_name} ──")
        print(f"  出场人物：{result[f'{pos}_cast']}")
        print(f"  依据句：{result[f'{pos}_source']}")
        print(f"  Prompt：{result[f'{pos}_prompt']}\n")

    print("========================\n")

    return result