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

---

## 陷阱五：`git show` 管道输出将 UTF-8 转为 UTF-16LE（高破坏性，2026-06-29 新增）

**触发条件**：在 PowerShell 中使用 `git show <commit>:<path> > file` 或 `git show | Select-String` 提取文件内容时。

**根本原因**：PowerShell 5.1 的管道和重定向操作符 (`>`, `|`) 默认将 stdout 输出按系统编码（Windows-1252/GBK）解码后再按 UTF-16LE 编码输出，导致 UTF-8 编码的中文被双重损坏。

**表现**：
- `git show` 输出的中文在文件中显示为乱码或字节混淆
- 文件大小膨胀（UTF-16LE 每个字符 2 字节）
- 含中文字符的 `.md` 文件在 git diff 中显示为完全重写
- 同一文件的 git 对象（`git cat-file -p` 或 Python subprocess）读取正确，但管道输出后损坏

**验证方法**：对比 `git show HEAD:file.md | wc -c` 和 `python3 -c "import subprocess; r=subprocess.run(['git','show','HEAD:file.md'],capture_output=True); print(len(r.stdout))"` —— 前者因 UTF-16LE 编码而尺寸翻倍。

**正确做法（已验证可靠）**：

**读文件**：永远用 Python 的 subprocess 获取原始字节，不用 PowerShell 管道：
```python
import subprocess
r = subprocess.run(["git", "show", "HEAD:writer/SKILL.md"], capture_output=True)
raw_bytes = r.stdout  # 原始 UTF-8 字节，无损
```

**写文件**：用 Python 的 `open(path, 'w', encoding='utf-8')` 写入：
```python
with open("output.md", "w", encoding="utf-8") as f:
    f.write(decoded_text)
```

**PowerShell 中的安全做法**：如果需要用 PowerShell 写 Python 脚本，用 `@' '@` here-string 配合 `Set-Content -Encoding UTF8`：
```powershell
$script = @'
import subprocess
# ... python code ...
'@
$script | Set-Content "script.py" -Encoding UTF8
```

---

## 陷阱六：write_file 写入的脚本文件在磁盘上不可访问（2026-06-29 新增）

**触发条件**：使用 `write_file` 工具写入 `.py` 脚本文件后，立即用 `python3 path/to/script.py` 执行。

**表现**：python3 报告 `can't open file: [Errno 2] No such file or directory`，即使 write_file 返回了 `resolved_path`。

**原因**：write_file 在 Windows 上的实现存在缓存/路径同步问题 —— 文件可能写入到了虚拟路径或尚未落盘。这是已知的 Windows 平台工具缺陷。

**正确做法**：
1. 写入后用 PowerShell 验证文件存在：`if (Test-Path "path/to/file") { Write-Output "OK" }`
2. 如果文件不存在，改用 PowerShell `Set-Content` 写入
3. 优先将 Python 脚本内容通过 PowerShell heredoc 传递并执行，而非依赖 write_file 落盘

```powershell
# 安全模式：heredoc + Set-Content
$script = @'
#!/usr/bin/env python3
print("hello world")
'@
$script | Set-Content "script.py" -Encoding UTF8
python3 script.py
```

---

## 陷阱七：上游 git 提交的中文编码深度损坏无法自动修复（2026-06-29 新增）

**触发条件**：从远端拉取的 git commit 中包含中文，但全部显示为乱码（如「网文」显示为「缃戞枃」）。尝试用 gb18030 回环修复或 ftfy 后仍残留 U+FFFD 替换字符。

**根本原因**：上游的 GBK 编码中文被以 UTF-8 编码存储到 git 对象中，但部分字节已被不可逆地修改（字节级损坏），不再是单纯的编码回环问题。例如「开」的 UTF-8 字节 `E5 BC 80` 被修改为 `E5 BC A2`（对应字符「弢」），导致任何编码转换都无法恢复原始内容。

**表现**：
- gb18030 回环修复（encode garbled→gb18030 → decode→utf-8）只能恢复约 94% 的字符
- ftfy 库对这类深度损坏无效
- 剩余 U+FFFD（约 5-6%）分布在标点符号和部分汉字中
- `git show` 直接在终端或文件中看到乱码，而非显示编码问题

**唯一可靠的修复方法——手工重建**：
1. 从 git 历史中找到最近的**干净提交**（无编码问题的版本）：`git log --all --oneline -- path/to/file`
2. 提取干净版本：`git show <clean-commit>:<path>`（通过 Python subprocess，**不是** PowerShell 管道）
3. 重构损坏提交中的增量内容（新增的段落、变更记录等），直接以正确的中文写入
4. 提交修复版本

```python
import subprocess

# 第一步：提取干净版本
r = subprocess.run(["git", "show", "clean-hash:file.md"], capture_output=True)
clean_text = r.stdout.decode("utf-8")

# 第二步：手动添加新内容的正确中文版本
clean_text += "\n## 新增内容\n正确的中文文本"

# 第三步：写回
with open("file.md", "w", encoding="utf-8") as f:
    f.write(clean_text)
```

**禁止做法**：
- ❌ 用 PowerShell 管道提取干净版本（会引入 UTF-16LE 损坏，参考陷阱五）
- ❌ 依赖任何自动修复工具（gb18030、ftfy、chardet）—— 字节级损坏无法自动恢复
- ❌ 在乱码文件上直接编辑保存（会固化损坏）

**教训**：
- 所有含中文的 git 操作（show、diff、log 输出重定向）**必须**通过 Python subprocess 完成，避免 PowerShell 管道介入
- 修复编码问题的提交应先以干净版本为 base 再添加增量，不要尝试修复乱码版本本身
