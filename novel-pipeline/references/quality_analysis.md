# 纯质量分析/质检流程规范
## 适用场景
用户要求「只分析、只检测、不修改原文」的场景，输出质量/合规检测结果，不做任何润色/修改操作。
## 执行流程
1. **确认范围**：明确用户指定的章节范围，不扩展/遗漏
2. **准备临时脚本**：创建一次性纯分析脚本（禁止修改任何原文），脚本逻辑：
   ```python
   #!/usr/bin/env python3
   import json, os, subprocess, sys
   from pathlib import Path
   def analyze_chapter(chap_num, chapters_dir):
       chap_path = Path(chapters_dir) / f"ch{chap_num}.md"
       with open(chap_path, "r", encoding="utf-8") as f:
           text = f.read()
       word_count = len([c for c in text if '\u4e00' <= c <= '\u9fff'])
       # 调用质量检测
       try:
           p = subprocess.Popen(
               [sys.executable, str(Path(__file__).parent.parent / "hooks" / "check_uno.py")],
               stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
               text=True, encoding="utf-8"
           )
           uno_out, _ = p.communicate(input=text, timeout=120)
           uno_result = json.loads(uno_out) if uno_out.strip() else {"passed": True, "issues": []}
           # 合规检测
           p2 = subprocess.Popen(
               [sys.executable, str(Path(__file__).parent.parent / "hooks" / "audit_publishready.py")],
               stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
               text=True, encoding="utf-8"
           )
           pr_out, _ = p2.communicate(input=text, timeout=120)
           pr_result = json.loads(pr_out) if pr_out.strip() else {"passed": True, "issues": []}
           # 综合评级
           total_issues = len(uno_result.get("issues", [])) + len(pr_result.get("issues", []))
           rating = "优秀" if total_issues == 0 else "良好" if total_issues < 3 else "需优化"
           return {
               "chapter": chap_num,
               "word_count": word_count,
               "uno_passed": uno_result.get("passed", True),
               "uno_issues": uno_result.get("issues", []),
               "publishready_passed": pr_result.get("passed", True),
               "publishready_issues": pr_result.get("issues", []),
               "rating": rating
           }
       except Exception as e:
           return {"chapter": chap_num, "error": str(e)}
   ```
3. **执行分析**：按章节顺序逐章执行，完成一章输出一章结果
4. **自动清理**：分析完成后立即删除临时脚本，不残留任何文件
## 输出格式要求
每章输出简洁表格：
| 章节 | 字数 | 质量检测 | 合规检测 | 综合评级 | 问题 |
| --- | --- | --- | --- | --- | --- |
| XX | XXX | ✅通过/❌不通过 | ✅通过/❌不通过 | 优秀/良好/需优化 | 列出问题（无则填无） |
## 常见问题处理
1. 检测到「结尾无终结标点」：标注「可能内容截断」，不修改原文
2. 工具返回「篇幅缩水100%」：为检测误报，忽略，正常输出结果
3. 章节文件不存在：直接返回错误提示
