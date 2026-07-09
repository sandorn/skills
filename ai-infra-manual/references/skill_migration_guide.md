# 自制Skill迁移到Git仓库标准流程
将自行开发的Skill纳入gitee版本管理，同时保持Hermes所有客户端正常使用的标准操作步骤，完全符合全局存储架构规则。
---
## 前置说明
### 存储架构规则
| 目录 | 作用 |
|------|------|
| A地物理存储 | `C:\Users\Administrator\AppData\Local\hermes\skills\` | Hermes所有版本共享的真实Skill存储目录 |
| Git仓库目录 | `C:\Users\Administrator\.agents\skills\` | 所有自制Skill的git版本管理根目录，同步到gitee.com/sandorn/skills |
| 目录联结 | A地的自制Skill目录均为junction映射指向Git仓库目录，无冗余副本 |
---
## 迁移操作步骤
### 第一步：确认Skill真实物理路径
执行命令获取Skill真实存储地址（注意LinkType=Junction的指向就是真实地址）：
```powershell
Get-Item "C:\Users\Administrator\AppData\Roaming\cn.org.hermesagent.desktop\runtime\hermes-home\skills\<分类>\<skill-name>" | Select-Object FullName, LinkType, Target
```
### 第二步：移动真实Skill目录到Git仓库
```powershell
# 移动真实文件到git仓库根目录
Move-Item -Path "<真实物理路径>" -Destination "C:\Users\Administrator\.agents\skills\<skill-name>" -Force
# 删除A地残留的空目录（如果有）
if (Test-Path "<A地原Skill路径>") { Remove-Item "<A地原Skill路径>" -Force -Recurse }
```
### 第三步：在A地创建junction目录联结
```powershell
New-Item -ItemType Junction -Path "<A地原Skill路径>" -Target "C:\Users\Administrator\.agents\skills\<skill-name>" -Force
```
### 第四步：验证可用性
执行`skill_view("<skill-name>")`，确认可以正常加载Skill内容，所有功能正常运行。
---
## 迁移后特性
✅ **多端共享**：CLI/Desktop/Web三个版本的Hermes自动共享该Skill，无需重复部署
✅ **修改同步**：修改Git仓库`~/.agents/skills/<skill-name>`下的内容，会自动同步到所有Hermes客户端
✅ **版本管理**：可直接在`~/.agents/skills`目录下执行git操作，提交到gitee仓库
✅ **无冗余存储**：全局只有一份真实代码，所有路径均为联结映射，无冗余副本
---
## 示例（本次ai-infra-manual迁移）
```powershell
# 1. 确认真实路径
Get-Item "C:\Users\Administrator\AppData\Roaming\cn.org.hermesagent.desktop\runtime\hermes-home\skills\devops\ai-infra-manual"
# 输出Target为 C:\Users\Administrator\AppData\Local\hermes\skills\devops\ai-infra-manual
# 2. 移动到git仓库
Move-Item -Path "C:\Users\Administrator\AppData\Local\hermes\skills\devops\ai-infra-manual" -Destination "C:\Users\Administrator\.agents\skills\ai-infra-manual" -Force
# 3. 创建A地联结
New-Item -ItemType Junction -Path "C:\Users\Administrator\AppData\Local\hermes\skills\devops\ai-infra-manual" -Target "C:\Users\Administrator\.agents\skills\ai-infra-manual" -Force
# 4. 验证
skill_view("ai-infra-manual")
```
