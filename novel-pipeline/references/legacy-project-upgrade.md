# 老版本 novel-pipeline 项目升级适配指南

## 适用场景
老版本（v1.x）小说项目升级到当前简化版流水线（v3.x）

## 关键变更
1. 移除 firstory / uno / publishready / memory-novel 依赖，仅保留 novel-deepseek + novel-doubao
2. 状态存储只走本地 `state-files/*.json`
3. 章节文件名统一 `ch001.md` 三位数补零
4. 环境变量集中在 Skill 本地 `.env`

## 升级步骤
1. **目录结构**
   - 根目录仅保留 `novel-pipeline.json`
   - 大纲移入 `outline/`
   - 状态文件统一存入 `state-files/`
   - 章节保持在 `chapters/`

2. **配置文件精简**
   `novel-pipeline.json` 只保留：
   ```json
   {
     "author": "作者名",
     "genre": "体裁",
     "auto_skip_transition_chapters": true,
     "outline_dir": "./outline/"
   }
   ```
   老版本里的 `firstory_ooc_check`、`publishready_audit`、`mcp_memory_novel_endpoint`、`state_storage_mode` 全部废弃删除。

3. **章节文件重命名**（仅覆盖 `chXX.md` / `chX.md` 数字格式）
   ```powershell
   # 遍历 chapters/ 下形如 ch1.md / ch01.md / ch123.md 的文件，统一为三位数补零
   # 如果你的旧文件是 "第X章_标题.md" 之类的中文格式，本脚本不会误改
   Get-ChildItem chapters\ch*.md | ForEach-Object {
       if ($_.Name -match '^ch(\d+)\.md$') {
           $n = [int]$matches[1]
           $new = "ch{0:D3}.md" -f $n
           if ($_.Name -ne $new) { Rename-Item $_.FullName $new }
       }
   }
   ```

4. **状态模板初始化**
   ```powershell
   Copy-Item <Skill路径>\state-files\*.json .\state-files\ -Force
   ```

5. **环境变量**
   在 `<Skill路径>\.env` 里补齐 6 个必需变量（见 `env-template.md`）。

## 验证升级成功
```powershell
python <Skill路径>\hooks\load_state.py
python <Skill路径>\scripts\verify_env.py
```
两条命令均返回 `loaded: true` / `summary.ok: true` 即完成升级。
