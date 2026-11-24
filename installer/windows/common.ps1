# common.ps1 - shared settings and helpers for the Windows tester kit.
# Must work in Windows PowerShell 5.1 (what Windows ships). Keep this file plain ASCII:
# 5.1 misreads other characters in files without a BOM.

$ShyftHome = Join-Path $HOME "Shyft"
$RepoUrl   = "https://github.com/timovreuxgerbier/agenthk.git"
$Models    = @("gemma4:e4b", "gemma4:e2b")          # Zippy, then Rick
$NeedGB    = 17                                     # measured on a fresh download: 9.5 + 7.5 GB
$Tests     = "tests.test_execute tests.test_golden tests.test_naming tests.test_caps tests.test_gate tests.test_two_models tests.test_cost tests.test_batch tests.test_server tests.test_zoom" -split " "
$OllamaDir = Join-Path $env:LOCALAPPDATA "Programs\Ollama"
$env:PYTHONUNBUFFERED = "1"                         # show Shyft's progress as it happens

function Say($t)  { Write-Host ""; Write-Host "==> $t" -ForegroundColor Green }
function Ok($t)   { Write-Host "    [ok] $t" -ForegroundColor Green }
function Warn($t) { Write-Host "    [!]  $t" -ForegroundColor Yellow }
function Stop-Shyft($t) { Write-Host ""; Write-Host "STOPPED: $t" -ForegroundColor Red; Read-Host "Press Enter to close this window" | Out-Null; exit 1 }
function Wait-Enter($t) { Read-Host $t | Out-Null }

# After winget installs something, this window doesn't know the new paths yet. This reloads them.
function Update-Path { $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User") }

function Get-WinBuild { [Environment]::OSVersion.Version.Build }
function Get-RamGB    { [math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB) }
function Get-FreeGB   { $d = (Get-Item $HOME).PSDrive.Name; [math]::Floor((Get-PSDrive $d).Free / 1GB) }
function Get-Gpus     { ((Get-CimInstance Win32_VideoController) | ForEach-Object { $_.Name }) -join ", " }

# "python" on a fresh Windows can be a shortcut to the Microsoft Store, not real Python: skip that one.
function Find-Python {
  foreach ($c in @("py", "python")) {
    $cmd = Get-Command $c -ErrorAction SilentlyContinue
    if ($cmd -and $cmd.Source -notlike "*WindowsApps*") {
      $v = & $c --version 2>&1
      if ("$v" -match "Python 3") { return $c }
    }
  }
  return $null
}
function Find-Ollama {
  $c = Get-Command ollama -ErrorAction SilentlyContinue
  if ($c) { return $c.Source }
  $p = Join-Path $OllamaDir "ollama.exe"
  if (Test-Path $p) { return $p }
  return $null
}
function Test-OllamaUp {
  try { Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 "http://127.0.0.1:11434/api/tags" | Out-Null; return $true } catch { return $false }
}
function Wait-Ollama { for ($i = 0; $i -lt 60; $i++) { if (Test-OllamaUp) { return $true }; Start-Sleep 2 }; return $false }
function Start-OllamaApp {
  $app = Join-Path $OllamaDir "ollama app.exe"
  if (Test-Path $app) { Start-Process $app } else { $o = Find-Ollama; if ($o) { Start-Process $o -ArgumentList "serve" -WindowStyle Hidden } }
}
function Test-Model($ol, $m) {
  foreach ($line in (& $ol list 2>$null | Select-Object -Skip 1)) { if ((("$line").Trim() -split "\s+")[0] -eq $m) { return $true } }
  return $false
}
