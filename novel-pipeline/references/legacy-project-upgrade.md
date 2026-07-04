# 老版本novel-pipeline项目升级适配指南
## 适用场景
老版本（v1.x）小说项目升级到v2.x+通用流水线的标准化流程

## 升级步骤
1. **目录结构优化**
   - 根目录仅保留`novel-pipeline.json`配置文件
   - 所有大纲文件移入`outline/`子目录
   - 所有辅助脚本移入`scripts/`子目录
   - 状态文件统一存入`state-files/`子目录
   - 章节保持在`chapters/`子目录
   
2. **配置文件升级**
   新增v2.x必填字段：
   ```json
   {
     "_comment": "升级适配新版novel-pipeline v2.1+",
     "author": "作者名",
     "genre": "体裁(xianxia/xuanhuan/dushi/kehuan等)",
     "publishready_audit": true,
     "firstory_ooc_check": true,
     "auto_skip_transition_chapters": true,
     "state_storage_mode": "local_file",
     "local_state_dir": "./state-files/",
     "outline_dir": "./outline/",
     "mcp_memory_novel_endpoint": "http://127.0.0.1:4000/mcp/memory_novel"
   }
   ```
   
3. **状态文件初始化**
   复制skill内置state-files模板到项目目录：
   ```powershell
   Copy-Item <Skill安装路径>\state-files\*.json <项目路径>\state-files\
   ```
   
4. **冗余文件清理**
   - 老版本硬编码API密钥的脚本移入scripts目录归档，不作为主流程使用
   - 移除根目录下零散的脚本、临时文件

## 验证升级成功
执行状态加载脚本无报错：
```powershell
python <Skill路径>\hooks\load_state.py
```
输出状态摘要（世界观/人物/伏笔/战力）即为升级完成。
