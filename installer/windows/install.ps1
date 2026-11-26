# install.ps1 - started by "1 Install Shyft.bat". Safe to run again: it skips what's done.
# Writes down everything it brings (record.txt), so "3 Remove Shyft" takes away only that.
$ScriptName = "1 Install"
. (Join-Path $PSScriptRoot "common.ps1")
. (Join-Path $PSScriptRoot "results.ps1")
Clear-Host
Write-Host @"
  Shyft installer ($KitVersion)
  ---------------
  This sets up Shyft for testing. It will:
    1. check your PC and start your results folder on the Desktop
    2. install Python if you don't have it (free, with Windows' own app installer)
    3. install Ollama (free, from ollama.com) if you don't have it
    4. download Rick's and Zippy's models (about 11 GB) if they aren't here yet
    5. unpack the Shyft code and the made-up test screenshots into a folder called Shyft
       (both come inside this kit; nothing else is downloaded for them)
  It only uses made-up screenshots. Nothing of yours is read or sent anywhere.
  Anything already on your PC stays as it is.
"@
Wait-Enter "Press Enter to start (or close this window to cancel)"

Say "1/6  Checking your PC"
Ensure-Results
Ok "Results folder ready: 'Shyft test results' on your Desktop"
if ((Test-Path $ShyftHome) -and (@(Get-Record "shyft_folder").Count -eq 0)) {   # checked first, before any download
  Stop-Shyft "There is already a folder called Shyft in your user folder that this kit didn't make. To keep it safe, the kit stops here and changes nothing. Rename or move that folder, then run this again."
}
$codeDone = (Test-Path (Join-Path $ShyftHome ".shyft_kit_commit"))     # kit files checked first, before any download
if (-not $codeDone -and -not (Get-ChildItem -Path $PSScriptRoot -Filter $CodeZipPattern -ErrorAction SilentlyContinue)) {
  Stop-Shyft "The Shyft code (a file named agenthk-$($CodeCommit.Substring(0, 7))...zip) is missing from the 'files' folder. Download the whole kit again and extract all of it."
}
if (-not $codeDone -and -not (Test-Path (Join-Path $PSScriptRoot "shyft_synthetic_set.zip"))) {
  Stop-Shyft "The test screenshots (shyft_synthetic_set.zip) are missing from the 'files' folder. Download the whole kit again and extract all of it."
}
$build = Get-WinBuild
if ($build -lt 19045) { Stop-Shyft "Ollama needs Windows 10 version 22H2 or newer. Please update Windows first." }
Ok "Windows (build $build)"
$ram = Get-RamGB
Ok ("{0}, {1} GB memory" -f (Get-CimInstance Win32_Processor | Select-Object -First 1).Name, $ram)
Ok ("Graphics: " + (Get-Gpus))
if ($ram -lt 5) { Stop-Shyft "Shyft can't run with $ram GB of memory (it needs at least 5 GB)." }
if ($ram -lt 8) {
  Warn "This PC has $ram GB of memory. Shyft may be very slow here, or may stop."
  Warn "That is exactly what we want to learn, so please carry on if you can."
  Note "Low memory: $ram GB (tester warned, continued)"
  Wait-Enter "Press Enter to continue"
}

Say "2/6  Checking free space"
$ol = Find-Ollama
if ($ol -and -not (Test-OllamaUp)) { Start-OllamaApp; Wait-Ollama | Out-Null }
$need = $MarginGB; $toGet = @()
foreach ($m in $Models.Keys) {
  if ($ol -and (Test-OllamaUp) -and (Test-Model $ol $m)) { continue }
  $need += $Models[$m]; $toGet += "$m ($($Models[$m]) GB)"
}
if (-not $ol) { $need += $OllamaGB; $toGet += "Ollama (about $OllamaGB GB)" }
$free = Get-FreeGB
if ($toGet.Count -gt 0) { Ok ("Still to download: " + ($toGet -join ", ")) }
if ($toGet.Count -gt 0 -and $free -lt $need) { Stop-Shyft ("Needs about {0} GB free, this PC has {1} GB. Free up some space, then run this again." -f [math]::Ceiling($need), $free) }
Ok ("{0} GB free, about {1} GB needed" -f $free, [math]::Ceiling($need))

Say "3/6  Python"
$py = Find-Python
if (-not $py) {
  if (-not (Get-Command winget -ErrorAction SilentlyContinue)) { Stop-Shyft "Python 3.11 or newer is missing. Install it from python.org (tick 'Add python.exe to PATH'), then run this again." }
  Write-Host "    Installing Python 3.12. A Windows window may ask for permission: click Yes."
  Add-Record "program" "Python 3.12 (Settings > Apps > Installed apps > Python 3.12 > Uninstall)"
  winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements --silent | Out-Null
  Update-Path; $py = Find-Python
  if (-not $py) { Stop-Shyft "Python didn't install. Install Python 3.11 or newer from python.org (tick 'Add python.exe to PATH'), then run this again." }
}
$pyVer = (& $py --version 2>&1 | Out-String).Trim()
Ok $pyVer; Set-PcLine "Python" $pyVer

Say "4/6  Ollama"
if (-not $ol) {
  Write-Host "    Installing Ollama with its official installer (no administrator needed)."
  Add-Record "program" "Ollama (Settings > Apps > Installed apps > Ollama > Uninstall)"
  powershell -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12; irm https://ollama.com/install.ps1 | iex"
  Update-Path; $ol = Find-Ollama
  if (-not $ol) { Stop-Shyft "Couldn't find Ollama after installing. Open Ollama once from the Start menu, then run this again." }
} else { Ok "Ollama was already here: using it as it is" }
if (-not (Test-OllamaUp)) { Start-OllamaApp }
if (-not (Wait-Ollama)) { Stop-Shyft "Ollama didn't start. Open it from the Start menu (llama icon by the clock), then run this again." }
Ok "Ollama is running"

Say "5/6  Rick's and Zippy's models"
foreach ($m in $Models.Keys) {
  if (Test-Model $ol $m) {
    if (@(Get-Record "model") -contains $m) { Ok "$m is here (downloaded by this kit earlier)" }
    else { Ok "$m was already on this PC: the kit will leave it there" }
    continue
  }
  Add-Record "model" $m                        # written BEFORE downloading, so even a half download is ours to remove
  Write-Host ("    Downloading {0} (about {1} GB). Keep the PC plugged in and online." -f $m, $Models[$m])
  & $ol pull $m
  if ($LASTEXITCODE -ne 0) { Stop-Shyft "The download of $m stopped. Run Install Shyft again: it picks up where it left off." }
  Ok "$m downloaded"
}
foreach ($m in $Models.Keys) {                # D27: exactly the measured builds, or stop and say so plainly
  $id = Get-ModelId $ol $m
  if ($id -ne $ModelIds[$m]) {
    $why = if (@(Get-Record "model") -contains $m) { "The kit downloaded it, but Ollama gave a different build." } else { "It was already on this PC, so the kit won't replace it." }
    Stop-Shyft ("{0} here is not the build Shyft was measured with (id {1}, expected {2}). {3} Please tell the Shyft team and send your results folder." -f $m, $id, $ModelIds[$m], $why)
  }
}
Ok "Both models are the exact builds Shyft was measured with"
Set-PcLine "Models" (($Models.Keys | ForEach-Object { "$_ ($($ModelIds[$_]))" }) -join ", ")
Save-OllamaInfo $ol

Say "6/6  Shyft code and test screenshots"
$mark = Join-Path $ShyftHome ".shyft_kit_commit"
if ((Test-Path $mark) -and ((Get-Content $mark -Raw).Trim() -eq $CodeCommit)) { Ok "Shyft code is already here" }
else {
  if (Test-Path $ShyftHome) { Remove-Item -Recurse -Force $ShyftHome }     # only ever our own, unfinished folder
  $zip = Get-ChildItem -Path $PSScriptRoot -Filter $CodeZipPattern -ErrorAction SilentlyContinue | Select-Object -First 1
  if (-not $zip) { Stop-Shyft "The Shyft code (a file named agenthk-$($CodeCommit.Substring(0, 7))...zip) is missing from the 'files' folder. Download the whole kit again and extract all of it." }
  $tmp = Join-Path $KitDir "unpack"; Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue
  New-Item -ItemType Directory -Force -Path $tmp | Out-Null
  try { Expand-Archive -Path $zip.FullName -DestinationPath $tmp -Force -ErrorAction Stop }
  catch { Stop-Shyft "Couldn't unpack the Shyft code. Download the whole kit again and extract all of it." }
  $src = Join-Path $tmp "agenthk-$CodeCommit"                          # GitHub names the folder after the full commit id
  if (-not (Test-Path $src)) { Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue; Stop-Shyft "The Shyft code in the kit isn't version $($CodeCommit.Substring(0, 7)). Ask the team for the right kit." }
  Add-Record "shyft_folder" $ShyftHome
  Move-Item -Path $src -Destination $ShyftHome
  Set-Content -Path $mark -Value $CodeCommit
  Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue
  Ok ("Shyft code unpacked (version {0})" -f $CodeCommit.Substring(0, 7))
}
$active = Join-Path $ShyftHome "golden\active_set.txt"
if ((Test-Path $active) -and ((Get-Content $active -Raw).Trim() -eq "synthetic")) { Ok "Made-up test screenshots already loaded" }
else {
  $zip = Join-Path $PSScriptRoot "shyft_synthetic_set.zip"
  if (-not (Test-Path $zip)) { Stop-Shyft "The test screenshots (shyft_synthetic_set.zip) are missing. Did you extract the whole download first?" }
  Expand-Archive -Path $zip -DestinationPath $ShyftHome -Force
  Push-Location $ShyftHome; & $py dev/use_set.py synthetic | Out-Null; $code = $LASTEXITCODE; Pop-Location
  if ($code -ne 0) { Stop-Shyft "Couldn't switch Shyft to the test screenshots." }
  Ok "91 made-up test screenshots ready"
}
$uiZip = Join-Path $PSScriptRoot "shyft_ui.zip"; $uiDst = Join-Path $ShyftHome "ui"   # Shyft's screens, shown after the test
if (Test-Path $uiZip) {
  try { Expand-Archive -Path $uiZip -DestinationPath $uiDst -Force -ErrorAction Stop; Ok "Shyft's screens ready" }
  catch { Warn "Couldn't unpack Shyft's screens. The test still works, but won't open the results page."; Note "shyft_ui.zip didn't unpack" }
} else { Warn "Shyft's screens (shyft_ui.zip) are missing. The test still works, but won't open the results page."; Note "shyft_ui.zip missing" }

Write-Host "    Running Shyft's own checks (about a minute)..."
Push-Location $ShyftHome
& $py -m unittest @Tests 2>&1 | ForEach-Object { Line-Text $_ } | Set-Content -Path (Join-Path $Out "install_check.txt")
$code = $LASTEXITCODE; Pop-Location
if ($code -eq 0) { Ok "All checks passed" } else { Warn "Some checks failed. That's still useful: see install_check.txt in your results folder."; Note "Some unit tests failed (install_check.txt)" }

Write-Host ""
Write-Host "Shyft is installed." -ForegroundColor Green
Write-Host "Next: double-click '2 Run the Shyft test'."
Wait-Enter "Press Enter to close"
