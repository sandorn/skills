# 封面生成

改编自 story-cover，适配图像生成工具。

---

## Step 1：收集信息

用 `clarify` 确认；若项目状态文件已有书名/题材，自动带入默认值：

- **书名**（必填）
- **作者名**（笔名，默认 Sandhill）
- **题材**（用于确定封面风格）
- **目标平台**：番茄小说 / 飞卢 / 起点 / 晋江 / 其他

---

## Step 2：确定封面风格

| 题材 | 推荐风格 |
|------|---------|
| 玄幻 | 暗色/金色字体 + 龙/剑/山脉 + 主角剪影 |
| 都市 | 明亮/都市天际线 + 主角人物 + 冷色调 |
| 仙侠 | 水墨/山水 + 古风人物 + 飘逸字体 |
| 科幻 | 科技感蓝紫 + 机械/星空 + 硬朗字体 |
| 恐怖 | 暗色/血红 + 阴影/怪物剪影 + 粗犷字体 |
| 历史 | 复古色调 + 地图/兵器 + 楷书/古风字体 |

---

## Step 3：生成封面

### 检测图像生成能力

优先检测当前环境是否对接了图像生成工具（MCP 或其他图像生成 API）：

```python
# 检测逻辑
def check_image_tool():
    """检测可用的图像生成工具"""
    tools = []
    # 检测常见 MCP 图像工具
    for tool_name in ['image_generate', 'image_gen', 'dalle', 'midjourney_mcp']:
        if tool_available(tool_name):
            tools.append(tool_name)
    return tools

available = check_image_tool()
```

### 路径 A：有图像生成工具

直接调用，生成封面：

```python
prompt = f"""
小说封面，竖版。
书名：{书名}
作者：{作者名}

风格要求：
- 题材：{题材}，{风格描述}
- 封面包含书名和作者名，文字清晰居中
- 专业网文封面风格，色彩饱和度适中
- 竖版构图，适合在线阅读平台
"""
# 调用可用的图像生成工具
```

生成后下载保存到本地：

```bash
curl -L -o "cover/{书名}_封面.png" "{生成的URL}"
```

### 路径 B：无图像生成工具

不伪造图片；改为输出可直接用于外部图像模型的提示词，保存到 `cover/{书名}_prompt.txt`：

```python
prompt = f"""
A Chinese web novel cover, vertical/portrait orientation.
Title: {书名}
Author: {作者名}

Style: {风格描述}
- Professional web novel cover art style
- Title and author name clearly centered
- {题材}-specific visual elements
- Moderate color saturation
- Portrait composition suitable for online reading platforms
- High quality, detailed illustration
"""
# 保存提示词
with open(f'cover/{书名}_prompt.txt', 'w') as f:
    f.write(prompt)
```

用户可将此提示词复制到 Midjourney / Stable Diffusion / DALL-E 等外部工具自行生成封面。

---

## Step 4：输出

封面图输出到 `cover/{书名}_封面.png` 或旧结构 `封面/{书名}_封面.png`。

如果图像生成工具返回的是 URL，先下载保存到本地：

```bash
# 使用 curl 下载
curl -L -o "cover/{书名}_封面.png" "{生成的URL}"

# 或使用 wget
wget -O "cover/{书名}_封面.png" "{生成的URL}"
```

---

## 多平台封面尺寸

| 平台 | 推荐尺寸 | 比例 | 格式 | 备注 |
|------|---------|------|------|------|
| 番茄小说 | 608 × 855 | 5:7 | PNG/JPG | 竖版，文字清晰居中 |
| 起点中文网 | 600 × 800 | 3:4 | JPG | 竖版，≤2MB |
| 飞卢 | 600 × 800 | 3:4 | JPG | 竖版 |
| 晋江 | 600 × 800 | 3:4 | JPG | 竖版，≤1MB |
| 通用 | 1200 × 1600 | 3:4 | PNG | 高清，可缩放至各平台 |

---

## 降级方案

如果当前环境没有图像生成工具：

1. 生成详细的图像生成提示词（prompt）保存为 `cover/{书名}_prompt.txt`
2. 提示词包含：书名、作者名、风格描述、构图要求、平台尺寸
3. 用户可将提示词复制到 Midjourney / Stable Diffusion / DALL-E 等外部工具生成

---

## 成功标准

- [ ] 封面包含书名 + 作者名
- [ ] 风格匹配题材
- [ ] 文件已保存到 `封面/` 目录
