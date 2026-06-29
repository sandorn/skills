# 设定一致性审查工作流（2026-06-26 新增）

本文档记录了在 Windows 环境下对网文项目进行设定一致性审查和修复的标准工作流。

---

## 适用场景

- 项目大纲完成，准备进入写作阶段
- 发现设定文件之间存在矛盾
- 需要对角色/势力/力量体系进行全面梳理

---

## 标准流程

### Step 1：读取所有设定文件

```powershell
# 获取文件列表
Get-ChildItem "$project\setting" -Name
Get-ChildItem "$project\outline" -Name

# 获取文件大小（行数）
Get-Content "$project\setting\story_bible.md" -Encoding UTF8 | Measure-Object -Line
```

### Step 2：使用 sub-agent 执行全面审查

调用 Claude Code CLI 或 sub-agent 执行：
1. 读取所有设定文件和大纲文件
2. 提取关键设定断言（数字、名字、时间、地点、规则）
3. 交叉对照，标记一致/矛盾
4. 按严重度分级（S1阻塞>S2内部矛盾>S3缺失>S4潜在风险）
5. 生成详细审查报告

### Step 3：应用修复

**S1/S2 级修复**（数值/名称/章节编号矛盾）：
```powershell
# 使用 PowerShell 正则替换
$filePath = "$project\outline\volume_02_chapter_outline.md"
$text = [System.IO.File]::ReadAllText($filePath, [System.Text.Encoding]::UTF8)
$text = $text.Replace("原始文本", "修复文本")
[System.IO.File]::WriteAllText($filePath, $text, [System.Text.Encoding]::UTF8)
```

**S3 级补充**（缺失内容）：
```powershell
# 追加新内容到现有文件
$filePath = "$project\setting\power_system.md"
$text = [System.IO.File]::ReadAllText($filePath, [System.Text.Encoding]::UTF8)
$addition = "`r`n## 新增章节标题`r`n`r`n补充内容..."
$text = $text + $addition
[System.IO.File]::WriteAllText($filePath, $text, [System.Text.Encoding]::UTF8)
```

### Step 4：验证修复

```powershell
# 验证修复是否生效
Select-String -Path "$project\outline\volume_02_chapter_outline.md" -Pattern "修复后的文本"
```

### Step 5：生成报告

**重要**：大型 Markdown 报告（>50行）**不要**用 `write_file` 工具写入，改用：

```powershell
$content = @"
# 标题

## 二级标题

内容...
"@
Set-Content -Path "$project\报告文件名.md" -Value $content -Encoding UTF8
```

---

## 审查维度

### S1 阻塞级（写作前必须修复）
- 设定文件之间数值矛盾
- 章节编号不一致
- 关键规则描述冲突

### S2 内部矛盾级
- 角色年龄/名称前后不一
- 认知边界与剧情发展矛盾
- 章节范围与实际章节号不符

### S3 缺失级
- 经济体系缺乏量化规则
- 升级时间线缺乏现实锚点
- 角色设定单薄
- 势力架构不完整

### S4 潜在风险级
- 等级开放说明不够清晰
- 卷间衔接需要验证

---

## 常见问题模式

| 问题 | 频率 | 建议 |
|------|------|------|
| 空间戒指容量矛盾 | 高 | 统一设定文件与章纲描述 |
| 属性数值精度不一致 | 中 | 统一使用整数百分比 |
| 章节编号范围错误 | 中 | 每次写章纲后验证章节号 |
| 角色认知边界过时 | 高 | 角色卡随剧情推进更新 |
| 经济体系量化缺失 | 高 | 提前建立量化表 |

---

## 输出文件

审查完成后应生成两个文件：
1. `审查报告-设定一致性.md`：详细审查报告（S1-S4分级）
2. `修复完成报告.md`：修复总结（修复统计+后续建议）
