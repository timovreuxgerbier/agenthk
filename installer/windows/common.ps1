# common.ps1 - shared settings and helpers for the Windows tester kit (kit 2).
# Must work in Windows PowerShell 5.1 (what Windows ships). Keep this file plain ASCII:
# 5.1 misreads other characters in files without a BOM.

$KitVersion = "kit 3.1"
$CodeCommit = "524117b648f9cbf0db445e4c43855dc028b19763"   # the ONE version of Shyft this kit tests (main, Nov 27: cloud lock, where-checks, Nook, records)
$CodeZipPattern = "agenthk-$($CodeCommit.Substring(0, 7))*.zip"   # GitHub "Download ZIP" of that commit, kept in files/
# Decision D27 (Nov 25): exactly these two model builds on every platform, checked by id after install.
# (The short names download different builds on a Mac.)
$Zippy      = "gemma4:e4b-it-q4_K_M"
$Rick       = "gemma4:e2b-it-q4_K_M"
$Models     = [ordered]@{ $Zippy = 6.6; $Rick = 4.6 }      # GB. Zippy's, then Rick's: 11.2 GB together
$ModelIds   = @{ $Zippy = "dc35e8d9c606"; $Rick = "b37049369adf" }   # the ID column of "ollama list"
$OllamaGB   = 4                                         # Ollama's docs: at least 4 GB for its own install
$MarginGB   = 2
$Tests      = "tests.test_execute tests.test_golden tests.test_naming tests.test_caps tests.test_gate tests.test_two_models tests.test_cost tests.test_batch tests.test_server tests.test_zoom tests.test_requirements tests.test_check_misses tests.test_cloud_lock tests.test_sync_check tests.test_disk_check tests.test_where_check tests.test_home tests.test_records" -split " "   # 169 tests (main 524117b)

$ShyftHome  = Join-Path $HOME "Shyft"
$KitDir     = Join-Path $env:LOCALAPPDATA "ShyftTesterKit"       # outside the Shyft folder, survives a failed install
$Record     = Join-Path $KitDir "record.txt"                     # what THIS kit brought, so Remove takes only that
$OllamaDir  = Join-Path $env:LOCALAPPDATA "Programs\Ollama"
$env:PYTHONUNBUFFERED = "1"                                       # show Shyft's progress as it happens
$ProgressPreference = "SilentlyContinue"                         # 5.1's progress bar makes downloads very slow
[Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12   # GitHub needs TLS 1.2
New-Item -ItemType Directory -Force -Path $KitDir | Out-Null

$Step = "starting"                                                # each script updates this; stops are logged with it
function Say($t)  { $script:Step = $t; Write-Host ""; Write-Host "==> $t" -ForegroundColor Green }
function Ok($t)   { Write-Host "    [ok] $t" -ForegroundColor Green }
function Warn($t) { Write-Host "    [!]  $t" -ForegroundColor Yellow }
function Wait-Enter($t) { Read-Host $t | Out-Null }
function Ask-YesNo($t) { while ($true) { $a = (Read-Host "$t (Y/N)").Trim().ToUpper(); if ($a -eq "Y") { return $true }; if ($a -eq "N") { return $false } } }

# What the kit brought: one "key=value" per line. Keys: shyft_folder, model, program.
function Add-Record($k, $v) { if (-not (@(Get-Record $k) -contains $v)) { Add-Content -Path $Record -Value "$k=$v" } }
function Get-Record($k) {
  if (-not (Test-Path $Record)) { return @() }
  @(Get-Content $Record | Where-Object { $_ -like "$k=*" } | ForEach-Object { $_.Substring($k.Length + 1) })
}

# After winget installs something, this window doesn't know the new paths yet. This reloads them.
function Update-Path { $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User") }

function Get-WinBuild { [Environment]::OSVersion.Version.Build }
function Get-RamGB    { [math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 1) }
function Get-FreeGB   { $d = (Get-Item $HOME).PSDrive.Name; [math]::Floor((Get-PSDrive $d).Free / 1GB) }
function Get-Gpus     { ((Get-CimInstance Win32_VideoController) | ForEach-Object { $_.Name }) -join ", " }

# Any real Python 3.11 or newer, wherever it comes from (python.org, Microsoft Store...).
# Tested by RUNNING it, not by its folder. Returns the full path of python.exe, or $null.
function Find-Python {
  foreach ($c in @(@("py", "-3"), @("python"), @("python3"))) {
    try {
      $pre = @(); if ($c.Count -gt 1) { $pre = $c[1..($c.Count - 1)] }
      $out = @(& $c[0] @pre -c "import sys; print(sys.version_info[0] * 100 + sys.version_info[1]); print(sys.executable)" 2>$null)
      if ($LASTEXITCODE -eq 0 -and $out.Count -ge 2 -and [int]$out[0] -ge 311) { return $out[1].Trim() }
    } catch { }
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
# Shyft's cloud lock asks Ollama (/api/status) whether its cloud is off, before every run. Ollama older than
# 0.40.17 can't answer, so every run would stop. The kit never updates Ollama: it checks and says so instead.
function Test-CloudReport {
  try {
    $s = (New-Object System.Net.WebClient).DownloadString("http://127.0.0.1:11434/api/status") | ConvertFrom-Json
    return ($s.cloud -ne $null) -and ($s.cloud.PSObject.Properties.Name -contains "disabled")
  } catch { return $false }
}
$TooOld = "Your Ollama is too old for this version of Shyft: it can't say whether its cloud is off, and Shyft checks that before every run. The kit never changes your Ollama, so please update it yourself from ollama.com/download, then run this again."
function Get-ModelId($ol, $m) {   # the model's id from "ollama list", or $null
  foreach ($line in (& $ol list 2>$null | Select-Object -Skip 1)) {
    $parts = ("$line").Trim() -split "\s+"
    if ($parts[0] -eq $m) { return $parts[1] }
  }
  return $null
}
function Test-HaveBuild($ol, $m) {   # the measured build is here under any name (e.g. gemma4:e4b): by id, D27
  foreach ($line in (& $ol list 2>$null | Select-Object -Skip 1)) { if ((("$line").Trim() -split "\s+")[1] -eq $ModelIds[$m]) { return $true } }
  return $false
}
function Test-Model($ol, $m) {
  foreach ($line in (& $ol list 2>$null | Select-Object -Skip 1)) { if ((("$line").Trim() -split "\s+")[0] -eq $m) { return $true } }
  return $false
}
