# 服务配置 YAML 安全变更流程（LiteLLM / MCP 场景）

> 适用：修改 `~/.litellm/config.yaml` 的 `mcp_servers:` 段、Hermes `config.yaml` 的 MCP/provider 段，
> 以及任何"改完要重启服务才生效、且服务启动时会做结构校验"的 YAML 配置。
>
> 本文是从一次真实事故中提炼的流程。**照着做可以避免把服务改挂。**

---

## 一、为什么需要专门流程

这类配置有两个特性，决定了不能"改完就重启"：

1. **服务启动时按 schema 强校验**——YAML 语法合法 ≠ 结构合法。解析通过但类型不对，
   服务会在启动阶段抛异常并退出，**连健康端点都起不来**。
2. **改错的代价是全量不可用**——不是"某个功能失效"，是整个网关 down，
   所有依赖它的客户端一起挂。

---

## 二、强制流程（六步，不跳步）

### ① 先备份

```powershell
$src = "C:\Users\Administrator\.litellm\config.yaml"
$bak = "$src.bak-<变更名>-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
Copy-Item $src $bak -Force
```

命名带**变更名 + 时间戳**，便于事后区分多次实验。回滚时直接 `Copy-Item $bak $src -Force`。

### ② 精确读取目标段，确认上下文

用 `read_file` 的 `offset/limit` 定位到目标行附近，**不要全局扫**。
同时用行号定位函数确认锚点：

```powershell
Select-String -Path "C:\Users\Administrator\.litellm\config.yaml" -Pattern "^\s{4}(officecli|git|yaml_lint)\s*:" |
  Select-Object LineNumber, Line
```

### ③ 用 `patch` 做外科手术式替换

只替换目标片段，带足上下文保证唯一匹配。不要整文件重写。

### ④ ⚠️ 结构校验（不是语法校验）

**这一步是本文的核心。** `yaml.safe_load` 通过**不代表服务能启动**。
必须额外校验"每个条目都是字典"这类结构性约束：

```powershell
python -c "import yaml; d=yaml.safe_load(open(r'C:\Users\Administrator\.litellm\config.yaml',encoding='utf-8')); m=d['mcp_servers']; print('YAML OK, MCP 数:', len(m)); print('目标项:', m['officecli']); bad=[k for k,v in m.items() if not isinstance(v,dict)]; print('非法条目:', bad if bad else '无')"
```

**判定标准**：`非法条目: 无` 才能进下一步。出现非空列表 → 立即回到 ③ 修正。

### ⑤ 重启服务

LiteLLM 有专用启动脚本，**必须用它**（直接启动会漏加载 `.env`，导致所有模型认证失败）：

```powershell
pwsh -NoProfile -File "C:\Users\Administrator\.litellm\start.ps1"
```

重启耗时较长，`background=true` + `notify_on_complete=true` 启动，避免阻塞。

### ⑥ 验证就绪 + 验证功能

**就绪**（进程 + 端点，两个都要看，缺一不可）：

```powershell
Get-Process litellm -ErrorAction SilentlyContinue | Select-Object Id, StartTime
try { Invoke-RestMethod -Uri "http://127.0.0.1:4000/health/liveliness" -TimeoutSec 15 } catch { "未就绪" }
```

**功能**：不要只验就绪就算完。**就绪 ≠ 你要改的那个功能可用**。
按变更目标做端到端调用验证（详见 `mcp-tool-discovery-verification.md`）。

---

## 三、真实事故复盘：加了一行非字典条目，整个网关起不来

### 事件

为了做"回滚对照实验"，在 `mcp_servers:` 段里临时加了一行**用于标记**的键：

```yaml
mcp_servers:
    ...
    officecli:
        command: npx
        args: [-y, officecli, mcp]
    officecli_probe_marker: TEMP_ROLLBACK   # ← 这一行
    git:
        ...
```

### 后果

YAML 语法完全合法，`yaml.safe_load` 通过。但服务**启动即崩溃**：

```
File "...\litellm\proxy\_experimental\mcp_server\mcp_server_manager.py", line 662, in load_servers_from_config
    _mcp_info: Dict[str, Any] = server_config.get("mcp_info", None) or {}
                               ^^^^^^^^^^^^^^^^^
AttributeError: 'str' object has no attribute 'get'

ERROR:    Application startup failed. Exiting.
```

`start.ps1` 的自动健康检查随之终止：

```
目标进程 (PID 15540) 已意外退出，健康检查终止
```

**整个网关 down**，所有 13 个 MCP server + 全部模型一起不可用。

### 根因

LiteLLM 加载 `mcp_servers:` 时，**假定每一个 key 的值都是 dict**（要调 `.get("mcp_info")`）。
任何字符串/标量值都会让 `.get` 抛 `AttributeError`。
—— 语法校验（YAML）和结构校验（schema）之间有一道鸿沟，**只有结构校验能拦住它**。

### 教训

1. **不要在受 schema 校验的段里放"标记用"的伪键**。做对照实验时，
   把标记写到**段外的注释**（`#` 行）或**独立的临时文件**里，不要污染数据结构。
2. **第 ④ 步的"非法条目"检查就是为拦住这个错而写的**——本次事故正是跳过了它。
3. 事故后**立即回滚并恢复服务**，然后如实向用户报告自己引入了失误。
   不要静默修复、不要轻描淡写成"环境问题"。

---

## 四、改动类型速查：哪些值形态是安全的

| 段 | 合法值形态 | 危险写法 |
|----|-----------|---------|
| `mcp_servers.<name>` | 必为 dict，含 `command`(str) / `args`(list) / `env`(dict) / `url`(str) | 任何标量值 → 启动崩溃 |
| `model_list` | list of dict，每项含 `model_name` / `litellm_params` | 标量项 → 启动崩溃 |
| Hermes `mcp_servers.<name>` | dict，含 `command`+`args` 或 `url`+`headers` | 同上 |

**通用判据**：不确定某键的值该是什么形态时，**参照同段内已有的同类条目照抄结构**，
不要凭直觉写。

---

## 五、Windows 路径在 YAML 中的写法

`mcp_servers` 里指定本地可执行文件时：

```yaml
    officecli:
        command: C:\Users\Administrator\AppData\Local\OfficeCli\officecli.exe
        args:
            - mcp
```

- **不要加引号**（YAML 裸标量可直接含 `:` `\`，只要 `:` 后不跟空格即可）。
  加了引号在部分解析器下会把 `\U` 当转义序列。
- **不要用正斜杠混写**——Windows 服务端 spawn 时原样传参，`\` 更稳。
- 校验时确认读出来的值没被转义破坏：`print(m['officecli'])` 应显示原始路径。
