# 网文风SOP — 可扩展文风规范模块

**版本:** 1.0
**用途:** 小说正文生成的文风基准，预留多文风扩展接口。
**调用方:** 写章管线、文风转换、润色脚本、质检红线。

---

## 设计原则

文风文件统一采用 **"预设 + 覆盖"** 模式：
- `presets/` 目录存放各平台/题材的文风预设（番茄、起点、知乎盐选等）
- 项目级 `writing_rules.md` 可以覆盖/扩展预设中的任何参数
- 脚本/管线通过 `style_profile` 参数选择预设

---

## 1. 文风预设接口

每个预设必须实现以下 6 个维度：

| 维度 | 字段名 | 说明 |
|------|--------|------|
| 读者画像 | `reader_profile` | 年龄、平台、阅读场景 |
| 禁令清单 | `bans` | 绝对禁止的词/句式/结构 |
| 句式参数 | `sentence_params` | 句长、段落、对话密度等量化指标 |
| 情绪规则 | `emotion_rules` | 情绪外化、爽点要素、钩子规则 |
| 对话规则 | `dialogue_rules` | 口语化程度、信息效率、标签使用 |
| 质检清单 | `quality_checks` | 生成后自检项 |

---

## 2. 预设：番茄爆款轻松逆袭风 (fanqie-quick-anti)

### 2.1 读者画像

```yaml
reader_profile:
  age_range: "18-35"
  platform: "番茄小说"
  reading_mode: "移动端，碎片化时间"
  core_demand: "即时情绪反馈，轻松爽快"
  genre: "都市游戏锚点、单人隐秘机缘、草根逆袭"
```

### 2.2 禁令清单（硬性阻断）

| 编号 | 类别 | 规则 | 严重级 |
|------|------|------|--------|
| B01 | 对话引号 | 必须使用 `「」`，禁用 `""` 或 `''` | P0 |
| B02 | 破折号 | 必须使用 `——`（两个全角），禁用 `--` `—` `…` | P0 |
| B03 | 句式污染 | 禁用 `不是…而是…` 结构 | P0 |
| B04 | 元叙事 | 禁用上帝视角总结（"他心中暗想""她感到一阵悲伤"） | P0 |
| B05 | AI高频词 | 禁用：然而、值得注意的是、综上所述、不禁、与此同时、换言之 | P0 |
| B06 | 成语堆砌 | 禁用四字成语连续使用、文言虚词（之乎者也） | P1 |
| B07 | 翻译腔 | 禁用翻译腔长句（多重定语从句式） | P1 |
| B08 | 章末说教 | 章节结尾禁止道德升华/哲理总结/预告下章 | P0 |
| B09 | 超长段落 | 禁止超过3行的连续段落 | P1 |
| B10 | AI过渡词 | 禁用：随着、紧接着、此刻、于是乎、最终 | P1 |

### 2.3 句式与节奏参数

```yaml
sentence_params:
  max_sentence_length: 15       # 单句≤15字占比≥70%
  max_paragraph_lines: 3        # 最大段落行数
  paragraph_separator: "空行"   # 段间分隔方式
  dialogue_ratio:
    min: 0.4                    # 对话行占本章≥40%
    max: 0.6                    # 对话行占本章≤60%
  action_priority: true         # 动作/感官描写优先于抽象形容
  short_sentence_dense: true    # 短句密集，节奏轻快
  no_literary_flourish: true    # 无冗长文艺描写
```

### 2.4 情绪与爽点规则

```yaml
emotion_rules:
  externalize: true             # 所有内心活动必须外化为行为/生理反应/台词
  cool_points:
    - "打脸即时性：反派嘲讽后300字内必须被打脸"
    - "收获具象化：升级/获宝后必须有具体数值变化或他人震惊反应"
    - "地位反差：通过配角态度转变侧面烘托主角成长"
  hook_rule:
    position: "last_100_chars"  # 章末最后100字必须设置悬念/冲突升级/新信息
    no_smooth_ending: true      # 禁止平稳收尾

character_archetype:
  personality: "冷静理智、沉稳隐忍、善于实测复盘"
  identity: "草根逆袭、低调发育、手握信息差"
  forbidden: "浮夸、中二、情绪化"
  core_appeal: "全世界唯我独有"

content_focus:
  - "强化独家秘密、独有特权、实测验证、细节爽点"
  - "弱化多余场景铺垫"
  - "聚焦男主独有系统优势、心理博弈、规则试探"
  - "每段测试对应明确结论"
  - "强化安全感、优势感、成长性"
  - "收尾留期待、埋后续升级伏笔"
```

### 2.5 对话写作规则

```yaml
dialogue_rules:
  colloquial: true              # 口语化：短句、语气词、省略主语
  role_appropriate: true        # 符合角色身份（混混不说书面语，大佬不说废话）
  info_efficiency: true         # 每句对话承载至少一项功能（推进/揭示/冲突/设定）
  ban_greetings: true           # 纯寒暄/水字数对话直接删除
  action_tag_instead_of_said: true  # 用动作衔接对话，减少"他说""她道"
```

### 2.6 输出质检清单

1. 全文无超过3行的段落
2. 对话占比 40%-60%
3. 无禁用词/句式
4. 章末有明确钩子
5. 所有情绪均已外化为行为/台词
6. 覆盖了所有节拍点
7. 中文字数 2500-3000
8. 无 AI 腔痕迹（可通过 6 项 GATE 检测）

---

## 3. 扩展方式

### 3.1 新增预设

在 `presets/` 目录下创建新的 YAML/MD 文件，实现上述 6 个维度接口。示例：

```
presets/
├── fanqie-quick-anti.md   # 番茄爆款轻松逆袭风（默认）
├── qidian-steady.md       # 起点稳健升级风（待扩展）
├── zhihu-short.md         # 知乎盐选短篇风（待扩展）
└── custom/                # 用户自定义预设
```

### 3.2 项目级覆盖

项目 `writing_rules.md` 可以覆盖任意预设参数：

```yaml
# writing_rules.md 示例
style_override:
  bans:
    B05_extra: ["猛然", "瞬间", "突然"]  # 追加项目级禁用词
  sentence_params:
    max_sentence_length: 12  # 更严格的句长限制
```

### 3.3 文风转换时的动态参数

文风转换脚本 (`scripts/polish.py`) 使用本 SOP 的 `content_focus` + `emotion_rules` 作为系统提示词核心，`sentence_params` + `bans` 作为质检校验依据。切换目标文风只需更换预设名称。

---

## 4. 与质检管线的集成

本 SOP 中的 `bans` 和 `quality_checks` 直接映射到 `quality.md` 的质检 Gate：

| SOP 维度 | 质检 Gate | 脚本 |
|----------|-----------|------|
| bans.B01-B05 | Gate 1: 硬禁令扫描 | `audit.py --ban-scan` |
| bans.B06-B10 | Gate 2: 软禁令+AI腔 | `audit.py --deslop` |
| sentence_params | Gate 3: 段落修复 | `split_paragraphs.py` |
| emotion_rules | Gate 4: 钩子/爽点检查 | `analyze_hook.py` |
| quality_checks 7-8 | Gate 5: 字数/全文验证 | `pad_chapter.py` |

---

## 5. 版本历史

- **1.0** (2026-06-30): 从 `style_guide.md` 和豆包润色提示词中抽象提取，建立 6 维接口，预留预设扩展机制。
