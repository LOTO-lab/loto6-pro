# backup.ps1
# ロト6 分析プラットフォームの主要ファイルをバックアップするスクリプト

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = "backup\$timestamp"

if (-not (Test-Path $backupDir)) {
    New-Item -ItemType Directory -Path $backupDir | Out-Null
}

$filesToBackup = @(
    "loto6_board_with_setball.html",
    "loto6_data.csv",
    "loto6_data_with_setball.csv",
    "logo_loto6pro.png",
    "loto6_template.html",
    "build_board.py"
)

foreach ($file in $filesToBackup) {
    if (Test-Path $file) {
        Copy-Item -Path $file -Destination $backupDir
        Write-Host "Backed up: $file to $backupDir"
    } else {
        Write-Warning "File not found: $file"
    }
}

Write-Host "Backup completed successfully at $backupDir" -ForegroundColor Green
