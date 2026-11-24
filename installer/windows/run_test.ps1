# run_test.ps1 - started by "2 Run the Shyft test.bat". Steps 2 to 5 of Sphinx's READ ME:
# Ollama with a longer memory window, memory log every 30 s, run A (two models) and run B (one model)
# with score and cost, then everything to send back in one folder on the Desktop.
. (Join-Path $PSScriptRoot "common.ps1")
Clear-Host
if (-not (Test-Path $ShyftHome)) { Stop-Shyft "Shyft isn't installed yet. Double-click '1 Install Shyft' first." }
$ol = Find-Ollama; $py = Find-Python
if (-not $ol -or -not $py) { Stop-Shyft "Something is missing. Double-click '1 Install Shyft' first." }
Write-Host @"
  Shyft test
  ----------
  Two runs on 91 made-up screenshots. Takes 30 to 90 minutes, mostly waiting.
    - Plug your PC in. It will stay awake by itself until the test ends.
    - Leave this window open. It can look frozen; it's working.
    - If something stops or the PC struggles, that's a result too: you'll still get a results folder.
"@
Wait-Enter "Press Enter to start"

$Out = Join-Path ([Environment]::GetFolderPath("Desktop")) "Shyft test results"
New-Item -ItemType Directory -Force -Path $Out | Out-Null
$start = Get-Date
Set-Location $ShyftHome
Remove-Item ps_timo.txt, run_A.txt, run_B.txt, (Join-Path $Out "what_happened.txt") -ErrorAction SilentlyContinue
$os = Get-CimInstance Win32_OperatingSystem; $cs = Get-CimInstance Win32_ComputerSystem
@("Date: $(Get-Date)",
  "Processor: $((Get-CimInstance Win32_Processor | Select-Object -First 1).Name)",
  "Memory: $(Get-RamGB) GB",
  "Graphics: $(Get-Gpus)",
  "PC model: $($cs.Manufacturer) $($cs.Model)",
  "Year you bought it (roughly): ____ please type it here",
  "Windows: $($os.Caption) $($os.Version)",
  "Free disk: $(Get-FreeGB) GB",
  "Python: $(& $py --version 2>&1)") | Set-Content (Join-Path $Out "my_pc.txt")

function Note($t) { Add-Content (Join-Path $Out "what_happened.txt") $t }
# Keeps the PC (and screen) awake while this window runs. Cleared again at the end.
function Set-Awake($on) {
  try {
    if (-not ("Shyft.Power" -as [type])) { Add-Type -Name Power -Namespace Shyft -MemberDefinition '[DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint f);' }
    if ($on) { [Shyft.Power]::SetThreadExecutionState([uint32]2147483651) | Out-Null }   # continuous + system + display
    else     { [Shyft.Power]::SetThreadExecutionState([uint32]2147483648) | Out-Null }   # back to normal
  } catch { if ($on) { Warn "Couldn't keep the PC awake by itself: please stop it from sleeping." } }
}
function Run-Step($label, [string[]]$pyArgs, $log) {
  Say $label
  & $py @pyArgs 2>&1 | ForEach-Object { $s = "$_"; Write-Host $s; if ($log) { Add-Content -Path $log -Value $s -Encoding UTF8 } }
  if ($LASTEXITCODE -eq 0) { Ok "done" } else { Warn "This step stopped. That's a result too."; Note "Stopped: $label ($(Get-Date))" }
}

$serve = $null; $job = $null
try {
  Say "Starting Ollama with a longer memory window"
  Get-Process -Name "ollama app", "ollama" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
  for ($i = 0; ($i -lt 15) -and (Test-OllamaUp); $i++) { Start-Sleep 1 }
  if (Test-OllamaUp) { Warn "Ollama didn't quit, so this test runs WITHOUT the longer memory window."; Note "Ran without OLLAMA_CONTEXT_LENGTH=16384 (Ollama didn't quit)" }
  $env:OLLAMA_CONTEXT_LENGTH = "16384"
  $serve = Start-Process -FilePath $ol -ArgumentList "serve" -WindowStyle Hidden -PassThru -RedirectStandardError (Join-Path $ShyftHome "ollama_serve.log")
  if (-not (Wait-Ollama)) { Stop-Shyft "Ollama didn't start. Restart your PC, then run the test again." }
  Ok "Ollama is running"
  Set-Awake $true

  $job = Start-Job -ArgumentList (Join-Path $ShyftHome "ps_timo.txt") -ScriptBlock {
    param($f)
    while ($true) {
      try { Add-Content $f ((New-Object System.Net.WebClient).DownloadString("http://127.0.0.1:11434/api/ps")) } catch { }   # always saved as text
      try {
        $o = Get-CimInstance Win32_OperatingSystem
        Add-Content $f ("System-wide memory free percentage: {0}%" -f [math]::Round($o.FreePhysicalMemory / $o.TotalVisibleMemorySize * 100))
      } catch { }
      Start-Sleep 30
    }
  }

  Run-Step "Run A: Rick (gemma4:e2b) with Zippy (gemma4:e4b)" @("run.py", "gemma4:e2b", "all", "--zippy", "gemma4:e4b") "run_A.txt"
  Run-Step "Scoring run A" @("run.py", "score") $null
  Run-Step "Cost of run A" @("run.py", "cost") $null
  Run-Step "Run B: Rick only (gemma4:e2b)" @("run.py", "gemma4:e2b", "all") "run_B.txt"
  Run-Step "Scoring run B" @("run.py", "score") $null
  Run-Step "Cost of run B" @("run.py", "cost") $null

  Say "Collecting your results"
  Get-ChildItem golden -File | Where-Object { $_.LastWriteTime -gt $start -and ($_.Name -like "cost_synthetic_*" -or $_.Name -like "score_synthetic_*") } | Copy-Item -Destination $Out
  Copy-Item ps_timo.txt, run_A.txt, run_B.txt -Destination $Out -ErrorAction SilentlyContinue
  $low = Select-String -Path ps_timo.txt -Pattern "free percentage: (\d+)" -ErrorAction SilentlyContinue | ForEach-Object { [int]$_.Matches[0].Groups[1].Value } | Sort-Object | Select-Object -First 1
  if ($low -ne $null) { Add-Content (Join-Path $Out "my_pc.txt") "Lowest free memory during the runs: $low%" }
} finally {     # runs even if the window is stopped with Ctrl+C
  if ($job) { Stop-Job $job -ErrorAction SilentlyContinue; Remove-Job $job -Force -ErrorAction SilentlyContinue }
  if ($serve) { Stop-Process -Id $serve.Id -Force -ErrorAction SilentlyContinue }
  Set-Awake $false
  Start-OllamaApp                                  # put Ollama back to normal
}
Ok ("{0} files in 'Shyft test results' on your Desktop" -f (Get-ChildItem $Out).Count)
Start-Process explorer.exe $Out
Write-Host ""
Write-Host "Done." -ForegroundColor Green
Write-Host "Type your PC's year in my_pc.txt, then send the whole 'Shyft test results' folder to Sphinx."
Write-Host "It holds only made-up file names, timings and model names."
Wait-Enter "Press Enter to close"
