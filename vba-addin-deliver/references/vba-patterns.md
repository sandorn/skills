# VBA 可复用代码模板

以下模板可直接复制到 `.bas` 模块中使用，`XXX` 替换为业务逻辑。

---

## 统一错误处理模板

```vba
Option Explicit

Public Sub MainProcedure()
    On Error GoTo ErrHandler
    
    ' === 业务逻辑 ===
    
    
    ' === 正常退出 ===
    Exit Sub
    
ErrHandler:
    LogError "MainProcedure", Err.Number, Err.Description, Err.Source
    MsgBox "操作失败：" & Err.Description, vbCritical, "错误"
End Sub
```

## 错误日志函数

```vba
Public Sub LogError(ByVal ProcName As String, _
                    ByVal ErrNum As Long, _
                    ByVal ErrDesc As String, _
                    ByVal ErrSrc As String)
    Dim ws As Worksheet
    On Error Resume Next
    Set ws = ThisWorkbook.Worksheets("_ErrorLog")
    If ws Is Nothing Then
        Set ws = ThisWorkbook.Worksheets.Add
        ws.Name = "_ErrorLog"
        ws.Visible = xlSheetHidden
        ws.Cells(1, 1).Value = "时间"
        ws.Cells(1, 2).Value = "过程"
        ws.Cells(1, 3).Value = "错误号"
        ws.Cells(1, 4).Value = "描述"
    End If
    On Error GoTo 0
    
    Dim r As Long
    r = ws.Cells(ws.Rows.Count, 1).End(xlUp).Row + 1
    ws.Cells(r, 1).Value = Now
    ws.Cells(r, 2).Value = ProcName
    ws.Cells(r, 3).Value = ErrNum
    ws.Cells(r, 4).Value = ErrDesc
End Sub
```

## 进度条更新（StatusBar）

```vba
Public Sub LongRunningProcess()
    Dim i As Long, total As Long
    total = 10000
    
    Application.ScreenUpdating = False
    Application.StatusBar = "处理中..."
    
    For i = 1 To total
        If i Mod 100 = 0 Then
            Application.StatusBar = "处理中... " & Format(i / total, "0%")
            DoEvents  ' 保持界面响应
        End If
        ' === 业务逻辑 ===
    Next i
    
    Application.StatusBar = False
    Application.ScreenUpdating = True
End Sub
```

## 批量读写（Variant 数组）

```vba
Public Sub FastReadWrite()
    Dim arr As Variant
    Dim i As Long, j As Long
    
    ' 一次性读入数组
    arr = Range("A1:D10000").Value
    
    ' 在内存中处理
    For i = LBound(arr, 1) To UBound(arr, 1)
        For j = LBound(arr, 2) To UBound(arr, 2)
            ' === 业务逻辑 ===
            arr(i, j) = arr(i, j) * 2  ' 示例：翻倍
        Next j
    Next i
    
    ' 一次性写回
    Range("A1:D10000").Value = arr
End Sub
```

## 后期绑定（避免引用丢失）

```vba
' ❌ 早期绑定——换机器可能报"无法找到项目或库"
' Dim dict As New Scripting.Dictionary

' ✅ 后期绑定——兼容所有机器
Public Function GetDictionary() As Object
    Set GetDictionary = CreateObject("Scripting.Dictionary")
End Function
```

## Settings 持久化（CustomDocumentProperties）

```vba
Public Function GetSetting(ByVal Key As String, Optional ByVal DefaultValue As String = "") As String
    On Error Resume Next
    GetSetting = ThisWorkbook.CustomDocumentProperties(Key).Value
    If Err.Number <> 0 Then GetSetting = DefaultValue
    On Error GoTo 0
End Function

Public Sub SaveSetting(ByVal Key As String, ByVal Value As String)
    On Error Resume Next
    ThisWorkbook.CustomDocumentProperties(Key).Value = Value
    If Err.Number <> 0 Then
        ThisWorkbook.CustomDocumentProperties.Add _
            Name:=Key, _
            LinkToContent:=False, _
            Type:=msoPropertyTypeString, _
            Value:=Value
    End If
    On Error GoTo 0
End Sub
```

## Ribbon 回调骨架

```vba
' customUI.xml 中 onAction="OnBtnRun" 对应的 VBA 过程必须为 Public
Public Sub OnBtnRun(ByVal control As IRibbonControl)
    MainProcedure
End Sub

' getLabel 回调（动态按钮文字）
Public Sub GetBtnLabel(ByVal control As IRibbonControl, ByRef returnedVal)
    returnedVal = "执行操作 (" & Format(Now, "HH:mm") & ")"
End Sub

' getEnabled 回调（动态禁用/启用按钮）
Public Sub GetBtnEnabled(ByVal control As IRibbonControl, ByRef returnedVal)
    returnedVal = (Len(Dir(ThisWorkbook.Path & "\data.xlsx")) > 0)
End Sub
```

---

> 📎 关联文件：[SKILL.md](../SKILL.md) · [build.ps1](../templates/build.ps1) · [rules.md](rules.md) · [delivery-checklist.md](delivery-checklist.md)
