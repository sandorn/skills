---
name: experiment
description: 实验全生命周期 — 规划、实现、运行、监控、分析、结果判读。触发词：实验方案、跑实验、deploy、monitor、分析结果、result to claim。
---

# Experiment — 实验管理

## 工作流

### 1. 实验规划 (experiment-plan)
从研究方案生成详细的 claim-driven 实验路线图。
触发：实验方案、experiment plan、ablation matrix

### 2. 代码实现 (experiment-bridge)
读取实验计划 → 实现代码 → 部署 GPU → 收集初始结果。
触发：实现实验、implement experiments、deploy the plan

### 3. 运行实验 (run-experiment)
部署到本地/远程/Vast.ai/Modal serverless GPU。
触发：run experiment、deploy to server、跑实验

### 4. 监控 (monitor-experiment / training-check)
检查 WandB 指标，捕获 NaN/发散/空闲 GPU。
触发：check results、monitor、is it done

### 5. 分析结果 (analyze-results)
统计、对比表、可视化。
触发：analyze results、compare、分析实验结果

### 6. 判读 (result-to-claim)
判断实验结果支撑哪些主张，哪些还需验证。
触发：result to claim、实验结果判读

## GPU 平台
- 启智平台 → qzcli skill
- vast.ai → vast-gpu skill
- Modal serverless → serverless-modal skill
