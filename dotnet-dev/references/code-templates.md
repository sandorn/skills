# C# 代码模板

## 

```csharp
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using Microsoft.Win32;
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading.Tasks;

namespace MyWpfApp.ViewModels
{
    public partial class MainViewModel : ObservableObject
    {
        [ObservableProperty]
        private string _logText = "";
        
        [ObservableProperty]
        private double _progress;
        
        [ObservableProperty]
        private string _selectedFile = "";
        
        [RelayCommand]
        private async Task SelectFileAsync()
        {
            var dialog = new OpenFileDialog
            {
                Filter = "Excel 文件|*.xlsx;*.xls|所有文件|*.*"
            };
            
            if (dialog.ShowDialog() == true)
            {
                SelectedFile = dialog.FileName;
                AddLog($"已选择文件：{dialog.FileName}");
            }
        }
        
        [RelayCommand]
        private async Task StartProcessAsync()
        {
            if (string.IsNullOrEmpty(SelectedFile))
            {
                AddLog("请先选择文件！");
                return;
            }
            
            try
            {
                AddLog("开始处理...");
                Progress = 0;
                
                // 业务逻辑在这里
                
                Progress = 100;
                AddLog("处理完成！");
            }
            catch (Exception ex)
            {
                AddLog($"处理失败：{ex.Message}");
            }
        }
        
        private void AddLog(string message)
        {
            LogText += $"{DateTime.Now:HH:mm:ss} - {message}{Environment.NewLine}";
        }
    }
}
```

## 

```csharp
using ClosedXML.Excel;
using System.Collections.Generic;
using System.Data;
using System.IO;

namespace MyWpfApp.Services
{
    public class ExcelService
    {
        public DataTable ReadExcel(string filePath)
        {
            using var workbook = new XLWorkbook(filePath);
            var worksheet = workbook.Worksheet(1);
            var dataTable = worksheet.CopyToDataTable();
            return dataTable;
        }
        
        public void MergeExcelFiles(List<string> files, string outputPath)
        {
            using var newWorkbook = new XLWorkbook();
            var newSheet = newWorkbook.Worksheets.Add("合并数据");
            
            int row = 1;
            bool hasHeader = false;
            
            foreach (var file in files)
            {
                using var workbook = new XLWorkbook(file);
                var worksheet = workbook.Worksheet(1);
                
                foreach (var row in worksheet.Rows())
                {
                    if (!hasHeader)
                    {
                        // 复制表头
                        int col = 1;
                        foreach (var cell in row.Cells())
                        {
                            newSheet.Cell(row.RowNumber(), col++).Value = cell.Value.ToString();
                        }
                        hasHeader = true;
                        row = 2;
                    }
                    else
                    {
                        // 复制数据行
                        int col = 1;
                        foreach (var cell in row.Cells())
                        {
                            newSheet.Cell(row.RowNumber(), col++).Value = cell.Value.ToString();
                        }
                        row++;
                    }
                }
            }
            
            newWorkbook.SaveAs(outputPath);
        }
    }
}
```

## 

```csharp
using HtmlAgilityPack;
using System.Net.Http;
using System.Threading.Tasks;
using System.Collections.Generic;

namespace MyWpfApp.Services
{
    public class WebScraperService
    {
        private readonly HttpClient _httpClient;
        
        public WebScraperService()
        {
            _httpClient = new HttpClient();
            _httpClient.DefaultRequestHeaders.Add("User-Agent", 
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36");
        }
        
        public async Task<string> GetHtmlAsync(string url)
        {
            return await _httpClient.GetStringAsync(url);
        }
        
        public async Task<List<string>> ExtractLinksAsync(string url)
        {
            var html = await GetHtmlAsync(url);
            var doc = new HtmlDocument();
            doc.LoadHtml(html);
            
            var links = new List<string>();
            var nodes = doc.DocumentNode.SelectNodes("//a[@href]");
            
            if (nodes != null)
            {
                foreach (var node in nodes)
                {
                    links.Add(node.GetAttributeValue("href", ""));
                }
            }
            
            return links;
        }
    }
}
```

