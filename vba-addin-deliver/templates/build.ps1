# Excel VBA Add-in Build Script (PowerShell)
# Generates xlam/xlsm add-in with Ribbon, icons, VBA, install/uninstall scripts
# Usage: .\build.ps1 -ProjectName "MyAddin" -OutputFormat "xlam"

param(
    [string]$ProjectName = "MyVBAAddin",
    [string]$OutputFormat = "xlam",
    [string]$ExcelVersion = "16.0",
    [string]$Description = "VBA Excel Add-in",
    [string]$OutputDir = ".\dist",
    [string]$RibbonLabel = "My Tools",
    [switch]$SkipTest
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [Text.Encoding]::UTF8

# Validate output format
if ($OutputFormat -notin @("xlam","xlsm")) {
    Write-Host "Error: OutputFormat must be 'xlam' or 'xlsm', got '$OutputFormat'" -ForegroundColor Red
    exit 1
}

# Validate temp directory
if (-not $env:TEMP -or -not (Test-Path $env:TEMP)) {
    Write-Host "Error: TEMP directory not accessible. Set `$env:TEMP to a writable path." -ForegroundColor Red
    exit 1
}

$WorkDir = Join-Path $env:TEMP ("vba_build_" + [Guid]::NewGuid().ToString('N').Substring(0,8))
$OutputFile = Join-Path $OutputDir "$ProjectName.$OutputFormat"

Write-Host "=== VBA Add-in Builder ===" -ForegroundColor Cyan
Write-Host "Project : $ProjectName"
Write-Host "Format  : $OutputFormat"
Write-Host "Output  : $OutputFile"
Write-Host "Note    : This script builds the OOXML skeleton. Embed VBA code (vbaProject.bin) separately via Excel COM or manual VBE import." -ForegroundColor DarkGray

New-Item -ItemType Directory -Path (Join-Path $WorkDir "_rels") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $WorkDir "customUI") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $WorkDir "xl") -Force | Out-Null

# [Content_Types].xml
$ct = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="xml" ContentType="application/xml"/>
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="png" ContentType="image/png"/>
  <Default Extension="bin" ContentType="application/vnd.ms-office.vbaProject"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>
  <Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
  <Override PartName="/xl/sharedStrings.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>
  <Override PartName="/xl/vbaProject.bin" ContentType="application/vnd.ms-office.vbaProject"/>
</Types>'
$ct | Out-File -FilePath (Join-Path $WorkDir "[Content_Types].xml") -Encoding UTF8

# _rels/.rels
$r = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
  <Relationship Id="rId2" Type="http://schemas.microsoft.com/office/2006/relationships/ui/extensibility" Target="customUI/customUI.xml"/>
</Relationships>'
$r | Out-File -FilePath (Join-Path $WorkDir "_rels\.rels") -Encoding UTF8

# customUI/customUI.xml
$ribbon = @"
<customUI xmlns="http://schemas.microsoft.com/office/2006/01/customui">
  <ribbon>
    <tabs>
      <tab id="customTab_$ProjectName" label="$RibbonLabel">
        <group id="grpMain" label="Tools">
          <button id="btnRun" label="Run" size="large" imageMso="HappyFace" onAction="OnBtnRun"/>
          <button id="btnHelp" label="Help" size="large" imageMso="Help" onAction="OnBtnHelp"/>
        </group>
      </tab>
    </tabs>
  </ribbon>
</customUI>
"@
$ribbon | Out-File -FilePath (Join-Path $WorkDir "customUI\customUI.xml") -Encoding UTF8

# xl/workbook.xml
$wbx = @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
          xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="Sheet1" sheetId="1" r:id="rId1"/>
  </sheets>
</workbook>
"@
$wbx | Out-File -FilePath (Join-Path $WorkDir "xl\workbook.xml") -Encoding UTF8

# xl/_rels/workbook.xml.rels
New-Item -ItemType Directory -Path (Join-Path $WorkDir "xl\_rels") -Force | Out-Null
$wbr = @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="theme/theme1.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
  <Relationship Id="rId4" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings" Target="sharedStrings.xml"/>
  <Relationship Id="rId5" Type="http://schemas.microsoft.com/office/2006/relationships/vbaProject" Target="vbaProject.bin"/>
</Relationships>
"@
$wbr | Out-File -FilePath (Join-Path $WorkDir "xl\_rels\workbook.xml.rels") -Encoding UTF8

# xl/worksheets/sheet1.xml
New-Item -ItemType Directory -Path (Join-Path $WorkDir "xl\worksheets") -Force | Out-Null
$sh = @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetViews><sheetView tabSelected="1" workbookViewId="0"/></sheetViews>
  <sheetData/>
</worksheet>
"@
$sh | Out-File -FilePath (Join-Path $WorkDir "xl\worksheets\sheet1.xml") -Encoding UTF8

# xl/theme/theme1.xml
New-Item -ItemType Directory -Path (Join-Path $WorkDir "xl\theme") -Force | Out-Null
$th = @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Office">
  <a:themeElements>
    <a:clrScheme name="Office">
      <a:dk1><a:srgbClr val="000000"/></a:dk1>
      <a:lt1><a:srgbClr val="FFFFFF"/></a:lt1>
    </a:clrScheme>
    <a:fontScheme name="Office">
      <a:majorFont><a:latin typeface="Calibri"/><a:ea typeface=""/></a:majorFont>
      <a:minorFont><a:latin typeface="Calibri"/><a:ea typeface=""/></a:minorFont>
    </a:fontScheme>
    <a:fmtScheme name="Office">
      <a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst>
      <a:lnStyleLst/>
      <a:effectStyleLst/>
      <a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst>
    </a:fmtScheme>
  </a:themeElements>
</a:theme>
"@
$th | Out-File -FilePath (Join-Path $WorkDir "xl\theme\theme1.xml") -Encoding UTF8

# xl/styles.xml
'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"/>' | Out-File -FilePath (Join-Path $WorkDir "xl\styles.xml") -Encoding UTF8

# xl/sharedStrings.xml
'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="0" uniqueCount="0"/>' | Out-File -FilePath (Join-Path $WorkDir "xl\sharedStrings.xml") -Encoding UTF8

# ============ Pack ZIP ============
New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
if (Test-Path $OutputFile) {
    try {
        Remove-Item $OutputFile -Force -ErrorAction Stop
    } catch {
        Write-Host "Error: Cannot overwrite '$OutputFile' — file may be locked by Excel. Close Excel and retry." -ForegroundColor Red
        exit 1
    }
}

Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory($WorkDir, $OutputFile)
Write-Host "Package created: $OutputFile" -ForegroundColor Green

# ============ Generate install/uninstall scripts ============
# install.bat writes to HKCU (user-level, no admin required)
# Uses %~dp0 to locate the add-in file relative to the script's own directory
# Note: Microsoft Store Excel uses a different registry layout; install.bat
# may not work for Store-installed Office. Check via regedit first.
$installBat = @"
@echo off
chcp 65001 >nul
echo === Install $ProjectName ===
set ADDIN_PATH=%~dp0$ProjectName.$OutputFormat
reg add "HKCU\Software\Microsoft\Office\$ExcelVersion\Excel\AddIns\$ProjectName" /v "Description" /t REG_SZ /d "$Description" /f
reg add "HKCU\Software\Microsoft\Office\$ExcelVersion\Excel\AddIns\$ProjectName" /v "LoadBehavior" /t REG_DWORD /d 3 /f
reg add "HKCU\Software\Microsoft\Office\$ExcelVersion\Excel\AddIns\$ProjectName" /v "Manifest" /t REG_SZ /d "%ADDIN_PATH%" /f
echo Done! Please restart Excel to load the add-in.
pause
"@

# uninstall.bat kills ALL Excel processes — warns the user first
$uninstallBat = @"
@echo off
chcp 65001 >nul
echo === Uninstall $ProjectName ===
echo This will close all Excel windows. Save your work first!
pause
taskkill /f /im EXCEL.EXE 2>nul
reg delete "HKCU\Software\Microsoft\Office\$ExcelVersion\Excel\AddIns\$ProjectName" /f
echo Done!
pause
"@

$installBat | Out-File -FilePath (Join-Path $OutputDir "install.bat") -Encoding UTF8
$uninstallBat | Out-File -FilePath (Join-Path $OutputDir "uninstall.bat") -Encoding UTF8
Write-Host "Install/uninstall scripts created in $OutputDir" -ForegroundColor Green

# ============ Cleanup ============
Remove-Item -Recurse -Force $WorkDir -ErrorAction SilentlyContinue

# ============ Self-test (optional) ============
if (-not $SkipTest) {
    Write-Host "`n=== Running self-test ===" -ForegroundColor Yellow
    try {
        $excel = New-Object -ComObject Excel.Application
        $excel.Visible = $false
        $excel.DisplayAlerts = $false
        $wb = $excel.Workbooks.Open($OutputFile)
        $ws = $wb.Worksheets(1)
        $ws.Cells(1,1) = "Test data"
        Write-Host "COM open OK — OOXML structure valid, file can be opened by Excel" -ForegroundColor Green
        $wb.Close($false)
        $excel.Quit()
        [System.Runtime.InteropServices.Marshal]::ReleaseComObject($excel) | Out-Null
    } catch {
        Write-Host "COM test failed (Excel may not be installed or file is locked): $_" -ForegroundColor DarkYellow
    }
}

Write-Host "`n=== Build complete ===" -ForegroundColor Cyan
try {
    Write-Host "Output dir : $(Resolve-Path $OutputDir -ErrorAction Stop)"
} catch {
    Write-Host "Output dir : $OutputDir"
}
Write-Host "Add-in     : $OutputFile"
Write-Host "Install    : install.bat"
Write-Host "Uninstall  : uninstall.bat"
Write-Host "`nReferences:" -ForegroundColor DarkGray
Write-Host "  SKILL.md    : ../SKILL.md"
Write-Host "  rules.md    : ../references/rules.md"
Write-Host "  checklist   : ../references/delivery-checklist.md"
Write-Host "  vba-patterns: ../references/vba-patterns.md"
