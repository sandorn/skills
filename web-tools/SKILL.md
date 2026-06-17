---
name: web-tools
description: "网页抓取与浏览器自动化：Scrapling 反爬引擎 + Apify Actor 部署。"
tags: [web, scraping, anti-bot, crawler, apify]
category: web
---

# Web Tools — 网页抓取与自动化

集成三大能力，精简为一个入口。

## 能力矩阵

| 能力 | 适用场景 | 工具/文档 |
|------|---------|----------|
| **高级反爬抓取** | Cloudflare Turnstile、JS 挑战、指纹检测 | Scrapling → `references/scrapling-guide.md` |
| **智能策略选择** | 自动发现 API、反封锁策略、Apify 部署 | web-scraper → `references/strategies/` `references/apify/` |
| **基础浏览器交互** | 页面导航、表单填写、截图、DOM 提取 | Hermes 内置 `browser_*` 工具 |

## 快速决策

```
用户说"抓取/爬取/提取数据"
  ├─ 有反爬(Cloudflare/JS挑战/403) → scrapling
  ├─ 要部署为 Apify Actor → web-scraper 策略 + apify/
  ├─ 仅需页面内容/截图/填表 → Hermes browser 工具
  └─ 不确定 → 先用 Hermes browser，被拦截后切 scrapling
```

## Scrapling 反爬引擎

核心能力：自适应解析、Cloudflare Turnstile 绕过、隐身浏览器模式。
详见 `references/scrapling-guide.md`（原始 scrapling-official 完整文档）。

**要求**: Python 3.10+, `pip install scrapling`

## 智能策略与 Apify

反封锁策略轮换、流量拦截 API 发现、Apify Actor 生产化部署。
详见 `references/strategies/` 和 `references/apify/`。

## 文件结构

- `references/scrapling-guide.md` — Scrapling 完整文档
- `references/strategies/` — 反封锁策略集合
- `references/apify/` — Apify Actor 部署指南
