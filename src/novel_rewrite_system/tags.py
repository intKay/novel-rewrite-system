"""最小标签词库 —— 创作控制标签的数据结构和默认词库。"""

from __future__ import annotations

from dataclasses import dataclass

CATEGORIES = ("情绪", "节奏", "人物关系", "文风", "剧情功能")


@dataclass(frozen=True)
class CreativeTag:
    """小说创作控制标签。"""

    name: str
    category: str
    description: str
    prompt_hint: str
    safety_note: str = ""
    fallback_hint: str = ""


_DEFAULT_TAGS = [
    # ── 情绪 ──
    CreativeTag(
        name="克制温柔",
        category="情绪",
        description="让续写保持含蓄温和的情感基调",
        prompt_hint="控制情感表达，保持含蓄温和的基调，避免激烈或极端表达。",
        fallback_hint="通过细腻的动作和环境描写传递含蓄情感。",
    ),
    CreativeTag(
        name="紧张压迫",
        category="情绪",
        description="营造悬疑和紧张感",
        prompt_hint="使用短句、急促呼吸、环境阴暗等元素制造紧张氛围。",
        safety_note="不依赖血腥或极端暴力。",
        fallback_hint="通过环境细节（阴影、声音、温度）和人物微反应暗示紧张。",
    ),
    CreativeTag(
        name="暗流涌动",
        category="情绪",
        description="表面平静下暗藏冲突与张力",
        prompt_hint="保持表面平静的对话或场景，但在细节中暗示人物之间的张力与未说出口的对抗。",
        fallback_hint="通过眼神、停顿、细微动作传递未言明的冲突。",
    ),
    # ── 节奏 ──
    CreativeTag(
        name="慢热铺垫",
        category="节奏",
        description="注重细节和氛围铺垫，不急推进剧情",
        prompt_hint="放慢节奏，增加环境描写、人物心理和细节刻画，为后续推进积累势能。",
    ),
    CreativeTag(
        name="快速推进",
        category="节奏",
        description="加快叙事节奏，减少描写，直接推进事件",
        prompt_hint="压缩描写和中间过程，直接呈现关键动作和对话，保持紧凑。",
    ),
    CreativeTag(
        name="反转收束",
        category="节奏",
        description="为当前段准备一个转折或揭晓",
        prompt_hint="在本段结尾制造一个意料之外的转折、真相揭露或情节反转。",
    ),
    # ── 人物关系 ──
    CreativeTag(
        name="试探拉扯",
        category="人物关系",
        description="人物之间相互试探、推拉，不直接说明意图",
        prompt_hint="对话中使用暗示、反话、沉默和肢体语言，体现人物间的试探与保留。",
        fallback_hint="通过对话中的潜台词和角色内心活动呈现试探感。",
    ),
    CreativeTag(
        name="误会加深",
        category="人物关系",
        description="让人物之间的误解进一步发酵",
        prompt_hint="利用信息差、错位对话或第三方干扰，加深人物之间的误会。",
    ),
    CreativeTag(
        name="信任建立",
        category="人物关系",
        description="人物之间逐渐建立信任或合作关系",
        prompt_hint="通过共同面对困难、分享秘密或互救等情节，让人物关系朝信任方向推进。",
    ),
    # ── 文风 ──
    CreativeTag(
        name="细腻描写",
        category="文风",
        description="不吝笔墨地渲染环境、动作和感受",
        prompt_hint="运用多感官描写（视觉、听觉、触觉、嗅觉），细致刻画环境、人物动作和内心感受。",
    ),
    CreativeTag(
        name="电影感镜头",
        category="文风",
        description="用画面式的叙述增强视觉感和场景感",
        prompt_hint="采用场景化的叙述方式，突出画面构图、光影变化和镜头移动感。",
    ),
    # ── 剧情功能 ──
    CreativeTag(
        name="埋下伏笔",
        category="剧情功能",
        description="为后续情节设置线索或暗示",
        prompt_hint="在正常叙述中自然植入一个看似无关但实际重要的细节、对话或物品，作为后续情节的伏笔。",
    ),
]


def get_default_tags() -> list[CreativeTag]:
    """返回默认标签词库的副本。"""
    return list(_DEFAULT_TAGS)


def format_tags_for_prompt(tags: list[CreativeTag]) -> str:
    """将选中的标签格式化为模型可读的创作控制提示文本。

    返回空字符串表示无标签。
    """
    if not tags:
        return ""

    by_category: dict[str, list[CreativeTag]] = {}
    for tag in tags:
        by_category.setdefault(tag.category, []).append(tag)

    lines: list[str] = []
    for category in CATEGORIES:
        if category not in by_category:
            continue
        lines.append(f"### {category}")
        for tag in by_category[category]:
            hint = tag.prompt_hint
            if tag.fallback_hint:
                hint += f"\n  （若具体表达受限，请改用：{tag.fallback_hint}）"
            lines.append(f"- **{tag.name}**：{tag.description}。{hint}")
        lines.append("")

    return "\n".join(lines)
