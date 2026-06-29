param(
    [string]$OutputPath = ""
)

$ErrorActionPreference = "Stop"

$rootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$clientDir = Join-Path $rootDir "client"
$sourcePath = Join-Path $clientDir "tray\CodexRemoteBridgeTray.cs"
if ([string]::IsNullOrWhiteSpace($OutputPath)) {
    $OutputPath = Join-Path $rootDir "CodexRemoteBridgeTray.exe"
}

if (-not (Test-Path -LiteralPath $sourcePath)) {
    throw "Tray source file not found: $sourcePath"
}

$outputDir = Split-Path -Parent $OutputPath
New-Item -ItemType Directory -Force -Path $outputDir | Out-Null

if (Test-Path -LiteralPath $OutputPath) {
    $trashDir = Join-Path $rootDir "trash"
    New-Item -ItemType Directory -Force -Path $trashDir | Out-Null
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $backupPath = Join-Path $trashDir "CodexRemoteBridgeTray-$timestamp.exe"
    Move-Item -LiteralPath $OutputPath -Destination $backupPath -Force
    Write-Host "Moved old EXE to: $backupPath" -ForegroundColor DarkYellow
}

Write-Host "Building tray EXE..." -ForegroundColor Cyan
Add-Type `
    -LiteralPath $sourcePath `
    -ReferencedAssemblies @(
        "System.dll",
        "System.Core.dll",
        "System.Drawing.dll",
        "System.Management.dll",
        "System.Windows.Forms.dll"
    ) `
    -OutputAssembly $OutputPath `
    -OutputType WindowsApplication

Write-Host "Build complete: $OutputPath" -ForegroundColor Green
Write-Host "Run it to show Codex Remote Bridge in the Windows tray area." -ForegroundColor Green
