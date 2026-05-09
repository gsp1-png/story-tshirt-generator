"""
测试模块 1：故事拆解
用《有身》前两段做冒烟测试
"""
import json
import sys
from pathlib import Path

# 让 Python 能找到 src/ 目录下的模块
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.story_parser import parse_story

# ── 测试用的故事文本（命题 A 节选，完整版后面再用）──
STORY = """
"吾所以有大患，为吾有身"，这句话里的"有身"不是指身体，
而是指自己的很多想法。

很多人过得不开心，是因为太在意"我"了，
比如我的财产、面子，这些都是烦恼的根源。

爸爸有很多白头发，去接哥哥放学时，
哥哥因为害羞不敢一起走——其实同学们根本不会在意这些，
都是哥哥自己想象出来的害怕。

妈妈打扮漂亮逛街，没人看她，她就怀疑衣服不好看，导致心情不好。

遇到烦心事时，要把自己当成别人，和万物融为一体，放下"小我"。

"无身"就是把自己和宇宙同频，这样很多烦恼自然就没了。
"""

print("=" * 50)
print("输入故事：")
print(STORY)
print("=" * 50)
print("⏳ 正在调用通义千问拆解故事...")

try:
    result = parse_story(STORY)
    print("\n✅ 拆解成功！\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))
except RuntimeError as e:
    print(f"\n❌ 出错了：{e}")
    sys.exit(1)