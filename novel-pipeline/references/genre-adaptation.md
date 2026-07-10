# 多题材适配指南

通用模板默认是字段无关设计，可适配几乎所有网文题材，以下是常见题材的配置参考：

---

## 适配方法
1. 初始化项目时，根据题材修改`state-files/power_system.json`，保留对应字段，删除不需要的字段
2. 人物档案`state-files/characters.json`中，根据题材替换能力字段名称
3. 在`novel.json`的`genre`字段填入对应题材标识

---

## 各题材参考配置

### 1. 仙侠/玄幻/修真
```json
// power_system.json 建议字段
{
  "power_levels": [
    {"name": "练气", "levels": 9, "lifespan_years": 120},
    {"name": "筑基", "phases": ["初期","中期","后期","圆满"], "lifespan_years": 300}
    // ... 其他境界
  ],
  "equipment_ranks": [
    {"rank": "凡阶", "grades": ["下品","中品","上品","极品"], "users": "练气-筑基"}
    // ... 其他装备等级
  ],
  "combat_rules": [
    "跨大境界战斗无法用数量弥补，除非有仙器/禁术/阵法加持"
    // ... 其他战斗规则
  ]
}

// characters.json 能力字段
"cultivation_level": "练气七层",
"special_abilities": ["飞剑术", "火系功法"]
```
**genre标识**: `xianxia` / `xuanhuan`

---

### 2. 都市异能/重生/系统流
```json
// power_system.json 建议字段
{
  "power_levels": [
    {"name": "E级", "description": "初级异能，力量/速度是常人3倍"},
    {"name": "D级", "description": "中级异能，可外放能量"}
    // ... 其他等级
  ],
  "system_mechanics": {
    "name": "XX系统",
    "currency": "积分/声望值",
    "sources": ["完成任务", "打脸反派", "升级奖励"]
  },
  "combat_rules": [
    "热武器对C级以上异能者无效",
    "精神类异能克制物理系"
    // ... 其他规则
  ]
}

// characters.json 能力字段
"ability_level": "D级巅峰",
"special_abilities": ["透视眼", "过目不忘"],
"system_points": 12500
```
**genre标识**: `dushi` / `yinen` / `xitong`

---

### 3. 科幻/末世/星际
```json
// power_system.json 建议字段
{
  "power_levels": [
    {"name": "基因锁一阶", "description": "基础基因解锁，体能翻倍"},
    {"name": "基因锁二阶", "description": "基因重组，获得超能力"}
    // ... 其他等级/机甲等级/文明等级
  ],
  "equipment_ranks": [
    {"rank": "民用级", "users": "普通民众"},
    {"rank": "军用级", "users": "正规军"}
    // ... 其他装备等级（机甲/战舰/武器）
  ],
  "tech_levels": [
    {"name": "行星级", "description": "可控核聚变，星际航行初级阶段"}
    // ... 其他科技等级
  ],
  "combat_rules": [
    "动能武器克制能量护盾",
    "曲率驱动无法在引力场中使用"
  ]
}

// characters.json 能力字段
"gene_level": "一阶解锁",
"equipment": ["战术外骨骼", "粒子手枪"],
"faction": "地球联邦军方"
```
**genre标识**: `kehuan` / `moshi` / `xingji`

---

### 4. 历史/架空/无超能力
```json
// power_system.json 建议字段
{
  "official_ranks": [
    {"name": "九品", "description": "县令级"},
    {"name": "八品", "description": "知府级"}
    // ... 其他官阶/身份等级
  ],
  "factions_strength": [
    {"name": "门阀世家", "power": "掌控地方经济人事"},
    {"name": "科举文官集团", "power": "掌控朝堂话语权"}
  ],
  "combat_rules": [
    "军队结阵可克制江湖高手",
    "古代战争后勤决定胜负"
  ]
}

// characters.json 能力字段
"official_rank": "正七品知县",
"skills": ["八股文", "断案", "剑术入门"],
"favor": 50 // 皇帝好感度/势力好感度等
```
**genre标识**: `lishi` / `chuanyue` / `wuxia`

---

### 5. 都市现实/言情/职场
*无超能力设定时，可直接删除`power_system.json`，流水线会自动跳过相关检查*

**genre标识**: `yanqing` / "zhichang" / "xiandai"

---

## 通用规则
1. 所有字段都可以根据需求自定义，模板字段只是参考，只要保持JSON结构合法即可
2. 新增自定义字段后，Agent会自动识别并带入上下文，无需修改Hook脚本
3. 如果不需要某个状态文件（比如无超能力文不需要power_system），直接删除即可，load_state会自动跳过不存在的文件
4. 伏笔/人物/世界观三个核心文件不建议删除，流水线依赖这三个文件做基础校验
