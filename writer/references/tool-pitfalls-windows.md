# Windows 环境工具陷阱

在 Windows 环境下使用 Hermes Agent 进行网文写作时的特有工具陷阱。

---

## 陷阱一：write_file 写入 Markdown 丢失换行符（高破坏性）

**触发条件**：在 Windows 环境下使用 `write_file` 工具写入 `.md` 文件时。

**原因**：`write_file` 在 Windows 上的实现会将内容作为单行写入，丢弃所有 `\r\n` 或 `\n` 换行符。写入的文件虽然字节数正确，但所有换行消失，变成一整行文本。

**表现**：
- 文件 `Get-Content` 显示为一整行（无回车）
- `Select-String` 搜索模式可能匹配不到（因为整个文件是一行）
- Markdown 标题 `##`、列表 `- `、表格 `|` 全部连在一起
- 文件大小正常但可读性为零

**正确做法**：
1. **写 Markdown 文件时优先用 terminal + PowerShell**，而非 `write_file`
2. 如果已用 `write_file` 写入且文件损坏，用 PowerShell 重新格式化
3. **验证写入**：写入后用 `Select-String` 或 `Get-Content | Select-Object -First 3` 确认换行正常

**预防措施**：
- 在 Windows 上写 `.md` 文件时，优先使用 `terminal` 执行 `python3 -c "..."` 多行写入
- 或用 `Set-Content -Path "file.md" -Value @("line1","line2") -Encoding UTF8`
- `write_file` 更适合写入 `.py`、`.json`、`.yaml` 等结构化文件

---

## 陷阱二：PowerShell 中文引号与 Invoke-Expression 冲突

**触发条件**：在 PowerShell 命令中使用含中文双引号 `""` 的字符串拼接。

**原因**：PowerShell 的 `Invoke-Expression` 或字符串插值会将 `"` 解析为特殊字符。

**表现**：`所在位置 行:1 字符: XXX\r\n+ ...` 报错，提示"表达式或语句中包含意外的标记"。

**正确做法**：
- 使用 Python 脚本处理含中文引号的文件操作
- 或用 PowerShell 时避免在字符串中嵌入中文引号，改用变量传递

---

## 陷阱三：Set-Content -NoNewline 丢失所有换行

**触发条件**：使用 `Set-Content -NoNewline` 写入文件时。

**原因**：`-NoNewline` 参数会阻止 PowerShell 在末尾添加换行符，但如果内容本身含 `\r\n`，行为取决于传入的字符串类型。

**正确做法**：
- 写多行文件时不用 `-NoNewline`
- 如需精确控制换行，用 `[System.IO.File]::WriteAllText()` 配合 `\r\n`

---

## 陷阱四：read_file 工具在 Windows 上的可靠性

**触发条件**：使用 `read_file` 工具读取大文件时。

**表现**：有时返回空结果或截断内容，尤其当文件路径含中文时。

**正确做法**：
- 含中文路径的文件优先用 `terminal` + `Get-Content -Encoding UTF8` 读取
- 验证读取结果：`Get-Content file.md | Measure-Object -Line`
