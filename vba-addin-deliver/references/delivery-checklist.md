# 交付前检查清单

## 代码质量
- [ ] Option Explicit 已声明
- [ ] 所有函数有错误处理（On Error GoTo）
- [ ] 无 ActiveWorkbook/ActiveSheet 裸引用
- [ ] 变量命名清晰，无单字母变量（循环计数器除外）
- [ ] 无硬编码路径（使用 ThisWorkbook.Path 或 Environ）
- [ ] 中文注释和字符串显示正常（UTF-8 BOM）

## Ribbon 完整性
- [ ] customUI/customUI.xml 存在且格式正确
- [ ] .rels 文件指向 customUI/customUI.xml
- [ ] [Content_Types].xml 注册了 xml 和 png 类型
- [ ] 图标文件存在且格式为 PNG
- [ ] Ribbon 按钮回调函数（onAction）对应的 VBA 过程存在
- [ ] getLabel/getImage 等回调函数已实现

## 打包
- [ ] 文件扩展名正确（xlam 或 xlsm）
- [ ] ZIP 内部路径结构正确（_rels、customUI、xl 同级）
- [ ] VBA 工程已保存（.bin 文件在 xl/ 下）
- [ ] 文件大小合理（不含未引用的资源）

## 安装卸载
- [ ] install.bat 双击即可执行，不需管理员权限
- [ ] uninstall.bat 可干净移除
- [ ] 脚本中包含 Excel 版本检测（2013/2016/2019/365）
- [ ] 路径包含空格时正确引用
- [ ] install.bat 会检查文件是否存在
- [ ] uninstall.bat 会先关闭 Excel 进程

## 功能测试
- [ ] 在 64 位 Excel 上运行通过
- [ ] 在 32 位 Excel 上运行通过（如可获取）
- [ ] Ribbon 按钮点击响应正常
- [ ] 核心功能对模拟数据产生正确结果
- [ ] 错误场景有提示信息（非静默失败）
- [ ] Excel 2016 最低版本上运行通过

## 用户体验
- [ ] 操作有明确反馈（MsgBox 或状态栏）
- [ ] 长时间操作有进度提示（Application.StatusBar）
- [ ] 可撤销操作前有警告
- [ ] 帮助/说明文档（如 README.txt）包含安装步骤
- [ ] 版本号清晰标注

## 交付物清单
- [ ] .xlam 或 .xlsm 主文件
- [ ] install.bat（安装脚本）
- [ ] uninstall.bat（卸载脚本）
- [ ] README.txt（使用说明）
- [ ] (可选) .ps1 构建脚本源码
- [ ] (可选) 图标源文件（.png）
