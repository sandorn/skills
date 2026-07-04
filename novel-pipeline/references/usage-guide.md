# novel-pipeline 使用指引

## 激活 Skill
技能安装完成后，使用 `/new` 重启会话即可生效。
首次使用在项目根目录执行 `python hooks/load_state.py` 确认状态加载正常。

## 标准写作流程

```
# 步骤 1: 初始化世界观
"帮我搭建一个<题材>世界观，核心设定+力量体系+主要势力"

# 步骤 2: 定义人物
"定义主角和主要配角的人设，包含性格/目标/底线"

# 步骤 3: 规划大纲
"规划第一卷的章节大纲，共X章"

# 步骤 4: 写章（触发完整流水线）
"写第1章"  → Agent 按流程执行：初稿生成→自检→润色→输出

# 步骤 5: 继续写
"写第2章"  → Agent 自动加载前一章的状态变更，继续写入
```

## 环境快速验证

一键全栈诊断（项目根目录执行）:
```powershell
python scripts/verify_env.py
```
输出包含：Python 版本、依赖包、密钥、MCP 服务文件、项目标记、章节统计。

逐项验证:
```powershell
# 加载状态
python hooks/load_state.py

# 测试参数校验
echo '{"arguments":{"global_setting":"测试","chapter_outline":"测试细纲至少十字以上","chapter_number":1}}' | python hooks/validate_draft.py
```

## 流水线验证
每章完成后检查：
1. `check_draft_quality` 输出 → `passed: true`
2. `audit_polish` 输出 → `passed: true`
3. `state-files/` 中 JSON 版本号递增
