# Git 中文编码修复方案

> **适用范围**：Git 仓库 .md 文件出现 GBK→UTF-8 双重编码损坏（字节级乱码）时。**不适用**：正常编码问题的排查——字节级损坏不可逆，不要在乱码文件上直接修复。
> **加载时机**：仅在确认发生编码损坏后。**紧急参考，非日常文档**。

## 根因

上游提交时中文以 GBK 编码写入，但 Git 以 UTF-8 方式存储。表现为：
- `git show` 输出的中文字符显示为「缃戞枃」之类乱码（而非「网文」）
- `.md` 文件中部分 ASCII 正常、部分中文乱码
- `ftfy` / `chardet` / gb18030 回环修复均无法完全恢复

## 诊断：确认是否为真正的编码损坏

用 Python 读取 git 对象，避免 PowerShell 管道干扰：

```python
import subprocess
r = subprocess.run(["git", "show", "HEAD:path/to/file.md"],
                   capture_output=True, cwd="repo_dir")
raw = r.stdout

# 检查是否含 U+FFFD（替换字符）
text = raw.decode("utf-8", errors="replace)
fffd_count = text.count("\ufffd")
print(f"FFFD: {fffd_count}")  # >0 表示损坏
```

> **注意**：`git show HEAD:file > out.md` 在 PowerShell 中会将 UTF-8 转为 UTF-16LE，导致文件大小翻倍。必须用 Python `subprocess` 获取原始字节。

## 唯一可靠的修复方案

### 原则
**不要试图修复乱码版本**。字节级损坏无法自动恢复。从历史中最后一个干净提交的版本重建。

### 步骤

1. **找到最后一个干净提交**。通常是引入新内容之前的版本：
   ```bash
   git log --oneline -- path/to/file.md
   ```

2. **用 Python 提取干净版本**：
   ```python
   import subprocess
   r = subprocess.run(
       ["git", "show", "COMMIT_HASH:path/to/file.md"],
       capture_output=True, cwd="repo_dir"
   )
   clean_text = r.stdout.decode("utf-8")
   ```

3. **识别乱码提交中的真实新增内容**。通过 changelog、diff 统计行数、阅读 gb18030 修复后的文本（尽管有残留 `�`，但语义可读）来理解新增的段落。

4. **将新增内容用正确中文手动写回干净版本**，而非从乱码版本复制。

5. **提交并推送**。

### 验证

```python
with open(file_path, "r", encoding="utf-8") as f:
    t = f.read()
assert "\ufffd" not in t, f"FFFD count: {t.count('\ufffd')}"
```

## 为什么其他方法不行

| 方法 | 效果 | 原因 |
|------|------|------|
| gb18030 回环修复 | 部分（~94%） | 部分字节已不可逆损坏 |
| gbk 回环修复 | 更少（~88%） | GBK 字符集覆盖更窄 |
| ftfy (`fix_text`) | 无效 | 字节级损坏非 mojibake，ftfy 针对编码解释错误 |
| `chardet` 自动检测 | 无效 | 文件已是合法 UTF-8（只是内容乱码） |
| 找上游修复 | 不可能 | commit 已推送，改写历史影响他人 |

## 禁止做法

- ❌ 用 PowerShell 管道提取干净版本（会引入 UTF-16LE 损坏）
- ❌ 依赖任何自动修复工具（gb18030、ftfy、chardet）—— 字节级损坏无法自动恢复
- ❌ 在乱码文件上直接编辑保存（会固化损坏）
- ❌ 用 `git show > file` 重定向（编码转换为 UTF-16LE）

## 教训

- 所有含中文的 git 操作（show、diff、log 输出重定向）**必须**通过 Python `subprocess` 完成，避免 PowerShell 管道介入
- 修复编码问题的提交应先以干净版本为 base 再添加增量，不要尝试修复乱码版本本身
