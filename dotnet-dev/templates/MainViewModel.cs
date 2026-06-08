using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using Microsoft.Win32;
using System;
using System.Collections.Generic;
using System.IO;
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
