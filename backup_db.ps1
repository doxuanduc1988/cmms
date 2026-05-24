# Script PowerShell để Backup Database CMMS cho việc di chuyển sang Docker
$BackupDir = "C:\CMMS\backup"
$DatabaseName = "CMMS"
$BackupFile = "$BackupDir\CMMS.bak"

# Tạo thư mục backup nếu chưa có
if (!(Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir
}

Write-Host "Đang sao lưu Database $DatabaseName..." -ForegroundColor Cyan

# Thực hiện lệnh SQL để backup
$SqlQuery = "BACKUP DATABASE [$DatabaseName] TO DISK = N'$BackupFile' WITH NOFORMAT, NOINIT, NAME = N'$DatabaseName-Full Database Backup', SKIP, NOREWIND, NOUNLOAD, STATS = 10"

# Thử kết nối với các instance phổ biến và phương thức xác thực khác nhau
$ServerNames = @(".\SQLSERVERTB2", "localhost\SQLSERVERTB2", ".\SQLEXPRESS", "(local)")

$success = $false
foreach ($server in $ServerNames) {
    Write-Host "Đang thử kết nối tới server: $server..." -ForegroundColor Gray
    
    # Cách 1: Thử bằng Windows Authentication (Quyền cao nhất của máy chủ)
    try {
        sqlcmd -S $server -E -Q $SqlQuery -b
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Sao lưu thành công bằng Windows Authentication!" -ForegroundColor Green
            $success = $true
            break
        }
    } catch {}

    # Cách 2: Thử bằng SQL Authentication (Tài khoản newsa)
    if (-not $success) {
        try {
            sqlcmd -S $server -U newsa -P cmms123 -Q $SqlQuery -b
            if ($LASTEXITCODE -eq 0) {
                Write-Host "Sao lưu thành công bằng tài khoản SQL newsa!" -ForegroundColor Green
                $success = $true
                break
            }
        } catch {}
    }
}

if (-not $success) {
    Write-Host "LỖI: Không thể kết nối với SQL Server. Vui lòng kiểm tra lại Instance Name hoặc quyền truy cập." -ForegroundColor Red
}
