# Windows 环境工具陷阱

�?Windows 环境下使�?Hermes Agent 进行网文写作时的特有工具陷阱�?

---

## 陷阱丢�：write_file 写入 Markdown 丢失换行符（高破坏��）

**触发条件**：在 Windows 环境下使�?`write_file` 工具写入 `.md` 文件时��?

**原因**：`write_file` �?Windows 上的实现会将内容作为单行写入，丢弃所�?`\r\n` �?`\n` 换行符��写入的文件虽然字节数正确，但所有换行消失，变成丢�整行文本�?

**表现**�?
- 文件 `Get-Content` 显示为一整行（无回车�?
- `Select-String` 搜索模式可能匹配不到（因为整个文件是丢�行）
- Markdown 标题 `##`、列�?`- `、表�?`|` 全部连在丢��?
- 文件大小正常但可读��为�?

**正确做法**�?
1. **�?Markdown 文件时优先用 terminal + PowerShell**，��非 `write_file`
2. 如果已用 `write_file` 写入且文件损坏，�?PowerShell 重新格式�?
3. **验证写入**：写入后�?`Select-String` �?`Get-Content | Select-Object -First 3` 确认换行正常

**预防措施**�?
- �?Windows 上写 `.md` 文件时，优先使用 `terminal` 执行 `python3 -c "..."` 多行写入
- 或用 `Set-Content -Path "file.md" -Value @("line1","line2") -Encoding UTF8`
- `write_file` 更��合写入 `.py`、`.json`、`.yaml` 等结构化文件

---

## 陷阱二：PowerShell 中文引号�?Invoke-Expression 冲突

**触发条件**：在 PowerShell 命令中使用含中文双引�?`""` 的字符串拼接�?

**原因**：PowerShell �?`Invoke-Expression` 或字符串插��会�?`"` 解析为特殊字符��?

**表现**：`扢�在位�?�?1 字符: XXX\r\n+ ...` 报错，提�?表达式或语句中包含意外的标记"�?

**正确做法**�?
- 使用 Python 脚本处理含中文引号的文件操作
- 或用 PowerShell 时避免在字符串中嵌入中文引号，改用变量传�?

---

## 陷阱三：Set-Content -NoNewline 丢失扢�有换�?

**触发条件**：使�?`Set-Content -NoNewline` 写入文件时��?

**原因**：`-NoNewline` 参数会阻�?PowerShell 在末尾添加换行符，但如果内容本身�?`\r\n`，行为取决于传入的字符串类型�?

**正确做法**�?
- 写多行文件时不用 `-NoNewline`
- 如需精确控制换行，用 `[System.IO.File]::WriteAllText()` 配合 `\r\n`

---

## 陷阱四：read_file 工具�?Windows 上的可靠�?

**触发条件**：使�?`read_file` 工具读取文件时��?

**表现**：有时返回空结果或截断内容，尤其当文件路径含中文时��?

**正确做法**�?
- 含中文路径的文件优先�?`terminal` + `Get-Content -Encoding UTF8` 读取
- 验证读取结果：`Get-Content file.md | Measure-Object -Line`

---

## 陷阱五：write_file / read_file 对中文路径完全静默失败（高破坏��）

**触发条件**：使�?`write_file` �?`read_file` 工具操作路径含中文的 `.md` 文件时��?

**表现**�?
- `write_file` 报告 `bytes_written: N`、`resolved_path: ...` 成功，但文件在磁盘上不存�?
- `read_file` 返回 `sed` �?PowerShell 错误，或被缓存内容覆盖，不反映实际文�?
- 此问�?**不是换行丢失**，是**整个文件根本没有写入/读不�?*

**根本原因**：工具内部路径处理对中文/多字节路径存在编码或转义问题，路径中的中文字符被转码后指向不存在的路径（�?`D:\\Writer\\xxxx` 实际写入到了某个虚拟/重定向位置）�?

**正确做法（已验证可靠�?*�?
1. **写文�?*：用 PowerShell `[System.IO.File]::WriteAllText()` 
2. **读文�?*：用 PowerShell `Get-Content -Encoding UTF8`
3. **�?Python 脚本**：先�?PowerShell `Out-File -Encoding UTF8` 写到不含中文的路径（�?`C:\Temp\`），�?`python C:\Temp\script.py`
4. **批量审计**：Python 脚本放到 `C:\Temp\`，用绝对路径引用项目文件

**禁止做法**�?
- �?`write_file` 写入含中文路径的任何文件
- �?`read_file` 读取含中文路径的任何文件
- �?`search_files` 搜索含中文路径的目录（同样静默失败）
- �?依赖 `write_file` 的返回结果判断文件是否写入成�?—��?必须�?`Get-Item` �?`Get-ChildItem` 验证

**验证写入**�?
```powershell
Get-Item "D:\Writer\项目名\chapters\ch_001.md" | Select-Object FullName, Length
```

---

## 陷阱六：read_file 工具�?Windows 上调�?sed 静默失败

**触发条件**：使�?`read_file` 工具读取文件时��?

**表现**：返回内容为丢��?sed 错误�?
```
sed : 无法�?sed"项识别为 cmdlet、函数��脚本文件或可运行程序的名称�?
```

**原因**：`read_file` �?Windows 上内部调�?`sed -n '1,500p' <file>` 来读取文件，�?Windows PowerShell 没有 `sed` 命令�?

**正确做法**�?
- 任何含中文路径或霢�要可靠读取的文件，用 `terminal` + `Get-Content -Encoding UTF8` 替代 `read_file`
- 示例：`Get-Content "D:\Writer\项目\chapters\ch_001.md" -Encoding UTF8`

---

## 陷阱七：search_files 工具在中文路径上静默失败

**触发条件**：使�?`search_files` 在含中文字符的路径下搜索文件或内容��?

**表现**：返回空结果�?`Path not found` 错误，即使路径确实存在��?

**原因**：`search_files` 底层使用 ripgrep，路径中的中文字符被转码后无法正确解析��?

**正确做法**�?
- �?`terminal` + `Get-ChildItem` 替代文件搜索
- �?`terminal` + `Select-String` 替代内容搜索
- 避免将含中文的路径传�?`search_files`