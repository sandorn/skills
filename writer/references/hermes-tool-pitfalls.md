# Hermes 工具陷阱

在 Hermes 环境中写章时需特别注意的工具交互陷阱。

---

## 陷阱一：write_file 污染（高破坏性）

**触发条件**：使用 `read_file` 读取文件后，将返回的 `content` 直接传给 `write_file` 覆写同一文件。

**原因**：Hermes 的 `read_file` 返回的 `content` 字段包含行号前缀，格式为 `"1|内容\n2|内容\n..."`。`write_file` 会原样写入，导致文件内容被线号前缀污染。

**表现**：文件字数骤降数百字（因为中文内容被 `N|` 等 ASCII 前缀替换），再次读取时正常但统计字数异常。

**正确做法**：
```
# ❌ 错误
r = read_file(path)
content = r['content']  # 包含 "1|..." 前缀
write_file(path, content)  # 文件被污染！

# ✅ 正确
r = read_file(path)
# 只用于读取，不写回
# 如需修改，使用 patch 工具
```

**修复已污染文件**：
```bash
sed -i 's/^[0-9]*|//' 被污染文件.md
```

---

## 陷阱二：terminal echo 中文转义

**触发条件**：在 `terminal` 工具中用 `echo` 追加中文内容到文件。

**原因**：bash 对含中文的长字符串可能触发转义错误，尤其是包含引号、括号等内容时。

**表现**：`unexpected EOF while looking for matching` 错误。

**正确做法**：
```
# ❌ 错误
echo "中文内容含"引号"..." >> file.md

# ✅ 正确
使用 execute_code 中的 Python open/write 追加
或以单引号包裹，避免 bash 解析引号
```

---

## 陷阱三：delegate_task 章节数量阈值

**阈值**：每批 10-15 章为宜。**超过 15 章几乎必触发** `max_iterations`（50次 API 调用上限）或 `timeout`（600s）。

**原因**：子代理每章需要 read→write→audit→patch 循环，章节数越多越早触及上限。

**策略**：
- 批量写章：每批 ≤15 章
- 批量审查：每批 ≤40 章（审查比写章省 API 调用）
- 委托返回后必须立即跑质检（禁令+字数），不信任自我报告

---

## 陷阱四：patch 工具的转义漂移

**触发条件**：在 `patch` 的 `old_string` 中包含引号（`"`）时。

**原因**：patch 工具的序列化层可能对引号做额外转义，导致 old_string 无法匹配文件原文。

**表现**：`Escape-drift detected` 或 `Could not find a match`。

**正确做法**：
- 在 old_string 中使用宽泛上下文定位，避免依赖引号精确匹配
- 如匹配包含引号的文本失败，改用 `terminal` + `sed` 替换
- 或用 `terminal` + Python 脚本直接写文件

---

## 陷阱五：echo >> 段落污染（高破坏性）

**触发条件**：用 `echo "长文本" >> chXX.md` 追加字数时，整段文本被当作**单行**写入（不带换行符）。

**原因**：bash 的 `echo` 默认不插入换行符号在不同平台表现不同。追加的白描文本即使语义上有多个句子，文件系统中仍是一行。

**表现**：`split_paragraphs.py` 扫描出数千行超长段落（>60字），全部来自最近追加的章节。本会话实际遭遇：5716 行超长段落，80% 由 `echo >>` 追加污染产生。

**正确做法**：
1. **永远不要在 Step 2 后跳过 Step 3**：`echo >>` 追加字数后**立即**跑 `split_paragraphs.py`
2. 优先用 `write_file` + Python 多行字符串追加，而非 `echo >>`
3. 如必须用 `echo`，每句一行，手动插入换行

```bash
# ❌ 错误
echo "他穿过走廊。灯光昏暗。走廊尽头是一个房间。" >> ch040.md
# → 整个追加为一整行，超 60 字

# ✅ 正确：分行追加
printf "他穿过走廊。\n灯光昏暗。\n走廊尽头是一个房间。\n" >> ch040.md
```

**修复已污染**：
```bash
python scripts/split_paragraphs.py --batch 正文/ --max-len 60
```

- `sed -i 's/——/，/g'` — 批量清除破折号（安全，不涉及编码问题）
- `execute_code` 中的 Python `open/write` — 完全可控
- `patch` 替换不含引号的短文本 — 可靠

---

## 陷阱六：write_file 转义引号残留（中破坏性）

**触发条件**：使用 `write_file` 写入含中文双引号 `"..."` 的内容时。

**原因**：Hermes 的 `write_file` 在序列化内容参数时，JSON 序列化器将 `"` 转义为 `\"`。如果工具在写入磁盘前未将 `\"` 还原为 `"`，文件中会出现 `\"走了。路通了。\"` 这样的转义残留。

**表现**：27+章中出现 `\"` 替代中文引号，集中在委托代理批量写章时出现（对话密度高的章更高发）。

**自动修复**：
```bash
# 扫描并修复所有转义引号
grep -l '\\"' 正文/ch*.md | while read f; do
    python3 -c "import sys;c=open(sys.argv[1]).read();open(sys.argv[1],'w').write(c.replace('\\\\\"','\"'))" "$f"
done
```

**预防**：
- `audit.py --fix-escaped` 内置转义引号检测+自动修复
- `pad_chapter.py` 写入后自动扫描并清除转义引号
- 质检流水线步骤7专门扫描此类残留
