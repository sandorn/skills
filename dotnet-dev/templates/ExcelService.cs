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
                
                foreach (var rowItem in worksheet.Rows())
                {
                    if (!hasHeader)
                    {
                        // 复制表头
                        int col = 1;
                        foreach (var cell in rowItem.Cells())
                        {
                            newSheet.Cell(rowItem.RowNumber(), col++).Value = cell.Value.ToString();
                        }
                        hasHeader = true;
                        row = 2;
                    }
                    else
                    {
                        // 复制数据行
                        int col = 1;
                        foreach (var cell in rowItem.Cells())
                        {
                            newSheet.Cell(rowItem.RowNumber(), col++).Value = cell.Value.ToString();
                        }
                        row++;
                    }
                }
            }
            
            newWorkbook.SaveAs(outputPath);
        }
    }
}
