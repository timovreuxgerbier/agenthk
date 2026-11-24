# run_test.ps1 - started by "2 Run the Shyft test.bat".
# Quick check first (3 screenshots) with a time estimate, then Run A and Run B, each followed by
# score and cost. Logs go straight into the results folder, so a stop at any point still leaves results.
$ScriptName = "2 Run test"
. (Join-Path $PSScriptRoot "common.ps1")
. (Join-Path $PSScriptRoot "results.ps1")
Clear-Host
Ensure-Results
if (-not (Test-Path (Join-Path $ShyftHome ".shyft_kit_commit"))) { Stop-Shyft "Shyft isn't installed yet. Double-click '1 Install Shyft' first." }
$ol = Find-Ollama; $py = Find-Python
if (-not $ol -or -not $py) { Stop-Shyft "Python or Ollama is missing. Double-click '1 Install Shyft' first." }
Write-Host @"
  Shyft test
  ----------
  First a quick check on 3 made-up screenshots (up to about 5 minutes). It tells you
  roughly how long the full test will take, and you decide whether to go on.
  The full test takes minutes on a PC with a graphics card, and possibly hours without one.

  Before you start:
    - This test closes and restarts Ollama. If you use Ollama for anything else, save that first.
    - Plug your PC in and keep the lid open. The PC stays awake by itself until the test ends.
    - Leave this window open. It can look frozen; it's working.
"@
Wait-Enter "Press Enter to start"

$serveLog = Join-Path $KitDir "ollama_serve.log"
function Set-Awake($on) {   # Windows' own "keep the PC awake" setting, cleared again at the end
  try {
    if (-not ("Shyft.Power" -as [type])) { Add-Type -Name Power -Namespace Shyft -MemberDefinition '[DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint f);' }
    if ($on) { [Shyft.Power]::SetThreadExecutionState([uint32]2147483651) | Out-Null } else { [Shyft.Power]::SetThreadExecutionState([uint32]2147483648) | Out-Null }
  } catch { if ($on) { Warn "Couldn't keep the PC awake by itself: please stop it from sleeping." } }
}
# Runs Shyft with the given arguments, shows its output and writes it straight into the results folder.
function Run-Step($label, [string[]]$pyArgs, $logName) {
  Say $label
  $log = $null; if ($logName) { $log = Join-Path $Out $logName; Remove-Item $log -ErrorAction SilentlyContinue }
  & $py @pyArgs 2>&1 | ForEach-Object { $s = Line-Text $_; Write-Host $s; if ($log) { Add-Content -Path $log -Value $s } }
  if ($LASTEXITCODE -eq 0) { Ok "done"; return $true }
  Warn "This step stopped. That's a result too."; Note "Step failed (exit code $LASTEXITCODE)"; return $false
}
function Run-Full($name, [string[]]$runArgs, $logName) {
  $since = Get-Date
  Run-Step "$name" $runArgs $logName | Out-Null
  Run-Step "Scoring $name" @("run.py", "score") $null | Out-Null
  Run-Step "Cost of $name" @("run.py", "cost") $null | Out-Null
  Copy-Reports $since                                 # saved now, before anything else can stop
}
function Show-Estimate($seconds) {
  $mins = [math]::Ceiling($seconds / 3 * 91 * 2 / 60)  # per screenshot, x 91 screenshots, x 2 runs
  $text = if ($mins -le 1) { "about 1 minute" } elseif ($mins -lt 90) { "about $mins minutes" } else { "about {0} hours" -f [math]::Round($mins / 60, 1) }
  Ok ("Quick check took {0} s. Rough estimate for the full test: {1}." -f [math]::Round($seconds), $text)
  Write-Host "    (The quick check includes loading the models, so the real test may go a bit faster.)"
  Set-PcLine "Rough estimate for the full test" $text
}

$serve = $null; $job = $null
try {
  Say "Restarting Ollama with a longer memory window"
  Get-Process -Name "ollama app", "ollama" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
  for ($i = 0; ($i -lt 15) -and (Test-OllamaUp); $i++) { Start-Sleep 1 }
  if (Test-OllamaUp) { Warn "Ollama didn't close, so this test runs WITHOUT the longer memory window."; Note "Ran without OLLAMA_CONTEXT_LENGTH=16384 (Ollama didn't close)" }
  $env:OLLAMA_CONTEXT_LENGTH = "16384"
  $serve = Start-Process -FilePath $ol -ArgumentList "serve" -WindowStyle Hidden -PassThru -RedirectStandardError $serveLog
  if (-not (Wait-Ollama)) { Stop-Shyft "Ollama didn't start. Restart your PC, then run the test again." }
  Ok "Ollama is running"
  Save-OllamaInfo $ol
  Set-Awake $true
  $job = Start-Job -ArgumentList (Join-Path $Out "ps_timo.txt") -ScriptBlock {   # memory sample every 30 s
    param($f)
    while ($true) {
      try { Add-Content $f ((New-Object System.Net.WebClient).DownloadString("http://127.0.0.1:11434/api/ps")) } catch { }
      try {
        $o = Get-CimInstance Win32_OperatingSystem
        Add-Content $f ("System-wide memory free percentage: {0}%" -f [math]::Round($o.FreePhysicalMemory / $o.TotalVisibleMemorySize * 100))
      } catch { }
      Start-Sleep 30
    }
  }
  Push-Location $ShyftHome

  $t = Get-Date
  $quickOk = Run-Step "Quick check: 3 screenshots, Rick and Zippy" @("run.py", "gemma4:e2b", "3", "--zippy", "gemma4:e4b") "quick_check.txt"
  $secs = ((Get-Date) - $t).TotalSeconds
  Set-PcLine "Quick check (3 screenshots, two models)" ("{0} s, {1}" -f [math]::Round($secs), $(if ($quickOk) { "finished" } else { "stopped" }))
  if ($quickOk) {
    Show-Estimate $secs
    if (Ask-YesNo "Run the full test now (Run A, then Run B)?") {
      Run-Full "Run A: Rick (gemma4:e2b) with Zippy (gemma4:e4b)" @("run.py", "gemma4:e2b", "all", "--zippy", "gemma4:e4b") "run_A.txt"
      Run-Full "Run B: Rick only (gemma4:e2b)" @("run.py", "gemma4:e2b", "all") "run_B.txt"
    } else { Note "Tester chose to stop after the quick check" }
  } else {
    Warn "The quick check with two models stopped. Trying Rick alone..."
    $t = Get-Date
    $oneOk = Run-Step "Quick check: 3 screenshots, Rick only" @("run.py", "gemma4:e2b", "3") "quick_check_one_model.txt"
    Set-PcLine "Quick check (3 screenshots, one model)" ("{0} s, {1}" -f [math]::Round(((Get-Date) - $t).TotalSeconds), $(if ($oneOk) { "finished" } else { "stopped" }))
    if ($oneOk -and (Ask-YesNo "Two models were too much for this PC, but one works. Run Run B (Rick only) now?")) {
      Run-Full "Run B: Rick only (gemma4:e2b)" @("run.py", "gemma4:e2b", "all") "run_B.txt"
    } elseif (-not $oneOk) { Note "Both quick checks stopped: Shyft could not run on this PC" }
    else { Note "Tester chose not to run Run B" }
  }
  Pop-Location
  $low = Select-String -Path (Join-Path $Out "ps_timo.txt") -Pattern "free percentage: (\d+)" -ErrorAction SilentlyContinue |
    ForEach-Object { [int]$_.Matches[0].Groups[1].Value } | Sort-Object | Select-Object -First 1
  if ($low -ne $null) { Set-PcLine "Lowest free memory during the runs" "$low%" }
} finally {     # runs even after Ctrl+C. (Closing the window with X skips this: see the READ ME.)
  if ($job) { Stop-Job $job -ErrorAction SilentlyContinue; Remove-Job $job -Force -ErrorAction SilentlyContinue }
  if ($serve) { Stop-Process -Id $serve.Id -Force -ErrorAction SilentlyContinue; Start-Sleep 1 }
  Save-ServeLog $serveLog
  Set-Awake $false
  Start-OllamaApp                                  # put Ollama back to normal
}
Write-Host ""
Write-Host "Done." -ForegroundColor Green
Write-Host "Your 'Shyft test results' folder on the Desktop now holds:"
Write-Host "  my_pc.txt (your PC, and the quick-check estimate), what_happened.txt (only if something stopped),"
Write-Host "  quick_check.txt, run_A.txt and run_B.txt (whatever ran), score_ and cost_ reports for each run,"
Write-Host "  ps_timo.txt (memory every 30 s), install_check.txt, ollama_info.txt and ollama_serve.log"
Write-Host "  (your Windows user name and home folder are replaced with <user> and <home>)."
Write-Host "Please type roughly when you bought the PC in my_pc.txt, then send the whole folder to Sphinx."
Start-Process explorer.exe $Out
Wait-Enter "Press Enter to close"
