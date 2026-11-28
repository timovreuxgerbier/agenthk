# results.ps1 - the "Shyft test results" folder on the Desktop. Every script uses this.
# Rules: the folder name never changes; my_pc.txt only ever GAINS lines; every stop is written down.

$desk  = [Environment]::GetFolderPath("Desktop")       # follows OneDrive if it moved the Desktop
if (-not $desk) { $desk = Join-Path $HOME "Desktop" }
$Out   = Join-Path $desk "Shyft test results"
$PcTxt = Join-Path $Out "my_pc.txt"

# Adds "Label: value" unless a line with that label is already there (never renames or removes one).
function Set-PcLine($label, $value) {
  if ((Test-Path $PcTxt) -and (Select-String -Path $PcTxt -SimpleMatch -Pattern "${label}:" -Quiet)) { return }
  Add-Content -Path $PcTxt -Value "${label}: $value"
}
# A new install, or a test on a PC whose results folder already holds a test: the earlier folder is kept,
# renamed with its date, so my_pc.txt starts fresh (its lines keep their first value). Nothing is deleted.
function Move-EarlierResults($why) {
  if (-not (Test-Path $Out)) { return }
  if ($why -eq "test" -and -not (Test-Path (Join-Path $Out "quick_check.txt"))) { return }
  $stamp = (Get-Item $Out).LastWriteTime.ToString("yyyy-MM-dd HHmm")
  $name = "Shyft test results (earlier $stamp)"
  for ($i = 2; Test-Path (Join-Path (Split-Path $Out) $name); $i++) { $name = "Shyft test results (earlier $stamp, $i)" }
  try { Rename-Item -Path $Out -NewName $name -ErrorAction Stop; Write-Host "  Your earlier results are kept on the Desktop as: $name" }
  catch { Write-Host "  Couldn't rename your earlier results folder (is it open?). Please close it, or rename it yourself, then start again."; Read-Host "  Press Enter to close"; exit 1 }
  if ($why -eq "test") {   # same install, new test: the install's own check still belongs with the new results
    $check = Join-Path (Join-Path (Split-Path $Out) $name) "install_check.txt"
    if (Test-Path $check) { New-Item -ItemType Directory -Force -Path $Out | Out-Null; Copy-Item $check $Out }
  }
}
# Creates the folder and the basic my_pc.txt lines. Safe to call again and again.
function Ensure-Results {
  New-Item -ItemType Directory -Force -Path $Out | Out-Null
  $os = Get-CimInstance Win32_OperatingSystem; $cs = Get-CimInstance Win32_ComputerSystem
  Set-PcLine "Date" (Get-Date)
  Set-PcLine "Kit" $KitVersion
  Set-PcLine "Shyft code commit" $CodeCommit
  Set-PcLine "Processor" (Get-CimInstance Win32_Processor | Select-Object -First 1).Name
  Set-PcLine "Memory" ("{0} GB" -f (Get-RamGB))
  Set-PcLine "Graphics" (Get-Gpus)
  Set-PcLine "PC model" "$($cs.Manufacturer) $($cs.Model)"
  Set-PcLine "Year you bought it (roughly)" "____ please type it here"
  Set-PcLine "Windows" "$($os.Caption) $($os.Version)"
  Set-PcLine "Free disk" ("{0} GB" -f (Get-FreeGB))
  Set-FolderIcon
}
# Gives the results folder the Shyft buddies icon. Windows needs: a hidden desktop.ini that names the icon,
# the icon inside the folder (so it still works after the kit is deleted), and the folder marked read-only
# (for folders that only means "has a custom look"; files inside can still be written).
# Only a nice touch: if anything here fails, the test carries on as normal.
function Set-FolderIcon {
  try {
    $ini = Join-Path $Out "desktop.ini"; $ico = Join-Path $Out "shyft.ico"
    if (Test-Path $ini) { return }                               # already done (safe to run twice)
    $src = Join-Path $PSScriptRoot "shyft.ico"
    if (-not (Test-Path $src)) { return }
    Copy-Item -Path $src -Destination $ico -Force
    Set-Content -Path $ini -Encoding ASCII -Value @("[.ShellClassInfo]", "IconResource=shyft.ico,0")
    & attrib.exe +h +s "$ico"
    & attrib.exe +h +s "$ini"
    & attrib.exe +r "$Out"
  } catch { }
}
# Every stop, in any script: which script, which step, why.
function Note($reason) {
  New-Item -ItemType Directory -Force -Path $Out | Out-Null
  Add-Content -Path (Join-Path $Out "what_happened.txt") -Value ("{0} | {1} | {2} | {3}" -f (Get-Date -Format "yyyy-MM-dd HH:mm"), $ScriptName, $Step, $reason)
}
function Stop-Shyft($t) {
  Note "STOPPED: $t"
  Write-Host ""; Write-Host "STOPPED: $t" -ForegroundColor Red
  Write-Host "This was written down in 'Shyft test results' on your Desktop. Please send that folder anyway."
  Read-Host "Press Enter to close this window" | Out-Null; exit 1
}
# Replaces the Windows user name and home path, so logs never carry who the tester is.
function Hide-User($text) {
  foreach ($p in @($env:USERPROFILE, $HOME)) { if ($p) { $text = $text -replace [regex]::Escape($p), "<home>" } }   # -replace ignores case, like Windows paths
  if ($env:USERNAME) { $text = $text -replace [regex]::Escape($env:USERNAME), "<user>" }
  return $text
}
function Save-OllamaInfo($ol) {
  if (-not $ol) { return }
  $f = Join-Path $Out "ollama_info.txt"
  Add-Content $f ("--- {0} ({1})" -f (Get-Date -Format "yyyy-MM-dd HH:mm"), $ScriptName)
  Add-Content $f (Hide-User ((& $ol --version 2>&1 | Out-String).Trim()))
  Add-Content $f (Hide-User ((& $ol list 2>&1 | Out-String).Trim()))
}
function Save-ServeLog($log) {
  if (Test-Path $log) { Set-Content -Path (Join-Path $Out "ollama_serve.log") -Value (Hide-User ((Get-Content $log -Raw) + "")) }
}
# Copies the score_ and cost_ reports Shyft wrote since $since into the results folder.
function Copy-Reports($since) {
  $g = Join-Path $ShyftHome "golden"
  if (-not (Test-Path $g)) { return }
  Get-ChildItem $g -File | Where-Object { $_.LastWriteTime -ge $since -and ($_.Name -like "score_synthetic_*" -or $_.Name -like "cost_synthetic_*") } |
    Copy-Item -Destination $Out
}

# One line of a program's output as plain text. (PowerShell wraps error lines; blank ones show as "RemoteException".)
function Line-Text($x) { $s = "$x"; if ($s -eq "System.Management.Automation.RemoteException") { "" } else { $s } }
