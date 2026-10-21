# Word COM 提取、页数校准与渲染验证

## 一、PowerShell 调用 Word COM 必须落地 .ps1

**症状**：把多行 Word COM 脚本内联传给 `terminal` 工具，报
`远程过程调用失败。 (0x800706BE)` 或 `OperationStopped`。

**原因**：Hermes 的 terminal 会经 `Invoke-Expression` 包装命令，多行脚本 + COM 释放逻辑在包装后失效。

**正确做法**：写入 `.ps1` 文件 → 用 `pwsh -NoProfile -File` 执行。

```powershell
# D:\TMP\extract.ps1
$ErrorActionPreference = 'Continue'
$src = "C:\...\某制度.doc"
$out = "D:\TMP\ref.txt"
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$doc = $word.Documents.Open($src)
$doc.SaveAs2($out, 2)    # 2 = wdFormatText
$doc.Close()
$word.Quit()
"OK $out"
(Get-Item $out).Length
```

```powershell
pwsh -NoProfile -File "D:\TMP\extract.ps1"
```

**要点**：
- `Documents.Open($src)` 不加 `[ref]` 参数——加了在包装环境下更易失败。
- `SaveAs2($out, 2)` 第二个参数用**裸整数**，不要 `[ref]2`。
- `$word.Quit()` 可能仍报 `0x800706BE`，但**前面的转换已完成**——检查输出文件是否存在即可，不必重试。
- 用 `Word.Application` 打开 `.pdf` 会失败（`null-valued expression`）；PDF 用 pymupdf。

---

## 二、页数校准（判断篇幅是否合理）

公文版式固定为 **A4 / 上37mm 下35mm 左28mm 右26mm / 三号字(16pt) / 固定行距30磅**。

```
每页行数 = (297-37-35)mm ÷ 30磅
        = 225mm ÷ 10.583mm ≈ 21 行/页
每行字数 ≈ 28 字
→ 每页容量 ≈ 588 字
```

**但实际页数远高于 `总字数 ÷ 588`**，因为每个段落的末行只填了一部分（平均浪费约半行）。

经验估算：

```
预估页数 ≈ (总字数 ÷ 588) + (段落数 × 0.5 ÷ 21)
```

**校准案例**：

| 文档 | 字数 | 段数 | 实测页数 |
|------|------|------|----------|
| 写字楼租赁管理办法（2026修订版） | 5635 | — | **16 页** |
| 采购管理办法（2026版）本稿 | 6656 | 183 | **18 页** |

> **结论：同一版式下，5000-7000 字的制度约 15-18 页是正常的。**
> 不要因为"看起来页数多"就砍内容——先与用户**同类既有制度**的页数对比。
> 反之，若用户期望"6 页"，须提示该版式的实际密度，请用户决定是精简内容还是接受页数。

### 取页数的脚本

```powershell
# D:\TMP\pages.ps1
$ErrorActionPreference = 'Continue'
$word = New-Object -ComObject Word.Application
$word.Visible = $false
foreach ($f in @("C:\...\制度A.docx", "C:\...\制度B.docx")) {
  if (-not (Test-Path $f)) { Write-Output "MISSING $f"; continue }
  try {
    $doc = $word.Documents.Open($f)
    $doc.Repaginate()
    "PAGES={0}  CHARS={1}  :: {2}" -f $doc.ComputeStatistics(2), $doc.ComputeStatistics(3), (Split-Path $f -Leaf)
    $doc.Close($false)
  } catch { "ERR " + $_.Exception.Message }
}
$word.Quit()
```

`ComputeStatistics(2)` = 页数；`ComputeStatistics(3)` = 字符数。
释放 COM 后 Word 可能残留进程，用 `Get-Process WINWORD | Stop-Process` 清理。

---

## 三、渲染验证（目视确认版式）

**不要只信 XML 检查**——`qa_docx.py` 通过后仍可能有视觉问题（行距、字体回退、层级不直观）。导出 PDF 再截图目视：

```powershell
# D:\TMP\mkpdf.ps1
$ErrorActionPreference = 'Stop'
$word = New-Object -ComObject Word.Application
$word.Visible = $false
foreach ($d in @("C:\...\制度.docx")) {
  $doc = $word.Documents.Open($d)
  $doc.Repaginate()
  $pdf = [System.IO.Path]::ChangeExtension($d, '.pdf')
  $doc.SaveAs2($pdf, 17)   # 17 = wdFormatPDF
  $doc.Close($false)
}
```

```python
# 截图前两页供目视
import fitz
d = fitz.open(r'C:\...\制度.pdf')
for i in (0, 1):
    d[i].get_pixmap(dpi=100).save(rf'D:\TMP\pv{i}.png')
```

然后用 `vision_analyze` 检查：字体是否落回宋体、行距是否异常、层级样式是否正确。

---

## 四、docx 结构速查（不依赖 Word）

```python
import zipfile, re, collections
z = zipfile.ZipFile(r'C:\...\制度.docx')
x = z.read('word/document.xml').decode('utf-8')
for sid, name in [('13','标题'),('14','H1'),('15','H2'),('16','H3'),('19','正文')]:
    print(sid, name, len(re.findall(r'<w:pStyle w:val="%s"/>' % sid, x)))
print('after :', collections.Counter(re.findall(r'w:after="(\d+)"', x)))
print('line  :', collections.Counter(re.findall(r'w:line="(\d+)"', x)))
```

---

## 五、Windows 终端铁律（本项目已反复踩）

1. 复杂脚本**先写 .ps1 落地文件再执行**，禁止单行内联。
2. PowerShell 字符串统一用 `@' '@` Here-String 包裹。
3. 所有文件 IO 强制 UTF-8：`-Encoding UTF8`；禁止 `>` 重定向写中文。
4. 优先 `pwsh.exe`（PS7），规避 5.1 转义缺陷。
5. **不要用 `python -c "..."` 传含正则/引号的代码** —— PowerShell 会吞掉 `\d` `"` 等符号，
   报 `The term '\d+' is not recognized`。**改为写 .py 文件再执行**。
6. 临时脚本文件名避免与标准库重名（曾用 `inspect.py` 导致 `import fitz` 时被自身遮蔽而报错）。
7. **`&` 会被误判为后台符号而拦截**。terminal 工具对含 `&` 的命令有防护，会直接返回
   `Foreground command uses '&' backgrounding` 而不执行——即使 `&` 出现在
   **字符串字面量或 `-join` 结果中**（如 `-join "\n"`、`cmd /c "a && b"`、URL 里的 `&`）。
   **对策**：把整段脚本用 `write_file` 落地成 `.ps1`，再用 `pwsh -NoProfile -File <路径>` 执行。
   不要试图转义或拆分规避——落地文件是唯一稳定的写法。
8. **不要用 `@' ... '@` Here-String 反向生成脚本**。用 Here-String 拼 `$变量`、
   `` `n ``、嵌套引号的脚本时极易出错，典型报错：
   `You must provide a value expression following the '-split' operator`。
   **对策**：直接用 `write_file` 写目标脚本正文（不经过 Here-String 包装层），
   Here-String 只用于**不含变量插值**的纯文本。
9. **前置 `Start-Sleep` 判断服务就绪要分段做**。单条命令里 `Start-Sleep 45` 后立即断言
   "未就绪"容易误判——刚重启的服务可能仍在初始化。改为多次短轮询，或先查进程列表
   （`Get-Process <name>`）再查健康端点，两者结合判断。
