---
name: notify
description: 飞书/Lark 通知 — 支持 Webhook 推送和双向交互模式。触发词：发飞书、notify feishu、飞书通知、Lark。

tags: [feishu,lark,webhook,notification]
category: communication
---

# Notify — 飞书通知

## 模式

### Webhook 推送
单向消息推送，适合状态更新/告警。
触发：发飞书、飞书通知

### 双向交互
飞书机器人对话，支持文档/表格/Bitable/审批流操作。
触发：飞书文档、feishu bot、Lark API

## 注意
- 需要已配置的飞书 Webhook URL 或 Bot Token
- 凭据通过环境变量或 MCP server 管理，不硬编码
