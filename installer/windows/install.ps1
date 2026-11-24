# install.ps1 - started by "1 Install Shyft.bat". Safe to run again: it skips what's done.
# Does the "Install" part of Sphinx's READ ME: Python and git, Ollama, the two models, the code, the test set.
. (Join-Path $PSScriptRoot "common.ps1")
Clear-Host
Write-Host @"
  Shyft installer
  ---------------
  This sets up Shyft for testing. It will:
    1. check your PC
    2. install Python and git if you don't have them (free, with Windows' own app installer)
    3. install Ollama (free, from ollama.com) if you don't have it
    4. download Rick's and Zippy's models (about 17 GB)
    5. put the Shyft code and the made-up test screenshots in a folder called Shyft
  It only uses made-up screenshots. Nothing of yours is read or sent anywhere.
"@
Wait-Enter "Press Enter to start (or close this window to cancel)"

Say "1/5  Checking your PC"
$build = Get-WinBuild
if ($build -lt 19045) { Stop-Shyft "Ollama needs Windows 10 version 22H2 or newer. Please update Windows first." }
Ok "Windows (build $build)"
Ok ("{0}, {1} GB memory" -f (Get-CimInstance Win32_Processor | Select-Object -First 1).Name, (Get-RamGB))
Ok ("Graphics: " + (Get-Gpus))
if ((Get-RamGB) -lt 8)  { Stop-Shyft ("Shyft needs at least 8 GB of memory. This PC has {0} GB." -f (Get-RamGB)) }
if ((Get-RamGB) -lt 16) { Warn "8 to 15 GB works, but runs may be slow. That's useful to know too." }
Ok ("{0} GB free disk space" -f (Get-FreeGB))

Say "2/5  Python and git"
$hasWinget = [bool](Get-Command winget -ErrorAction SilentlyContinue)
$py = Find-Python
if (-not $py) {
  if (-not $hasWinget) { Stop-Shyft "Python is missing. Install it from python.org (tick 'Add python.exe to PATH'), then run this again." }
  Write-Host "    Installing Python. A Windows window may ask for permission: click Yes."
  winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements --silent | Out-Null
  Update-Path; $py = Find-Python
  if (-not $py) { Stop-Shyft "Python didn't install. Install it from python.org (tick 'Add python.exe to PATH'), then run this again." }
}
Ok (& $py --version 2>&1)
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
  if (-not $hasWinget) { Stop-Shyft "git is missing. Install it from git-scm.com, then run this again." }
  Write-Host "    Installing git. A Windows window may ask for permission: click Yes."
  winget install -e --id Git.Git --accept-package-agreements --accept-source-agreements --silent | Out-Null
  Update-Path
  if (-not (Get-Command git -ErrorAction SilentlyContinue)) { Stop-Shyft "git didn't install. Install it from git-scm.com, then run this again." }
}
Ok (git --version)

Say "3/5  Ollama"
if (-not (Find-Ollama)) {
  Write-Host "    Installing Ollama with its official installer (no administrator needed)."
  powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://ollama.com/install.ps1 | iex"
  Update-Path
}
$ol = Find-Ollama
if (-not $ol) { Stop-Shyft "Couldn't find Ollama after installing. Open Ollama once from the Start menu, then run this again." }
if (-not (Test-OllamaUp)) { Start-OllamaApp }
if (-not (Wait-Ollama)) { Stop-Shyft "Ollama didn't start. Open it from the Start menu (look for the llama icon by the clock), then run this again." }
Ok "Ollama is running"

Say "4/5  Rick's and Zippy's models"
foreach ($m in $Models) {
  if (Test-Model $ol $m) { Ok "$m is already here"; continue }
  if ((Get-FreeGB) -lt 10) { Stop-Shyft "Not enough free space for $m. Free up space (about $NeedGB GB in total), then run this again." }
  Write-Host "    Downloading $m. This is the long part; keep the PC plugged in and online."
  & $ol pull $m
  if ($LASTEXITCODE -ne 0) { Stop-Shyft "The download of $m stopped. Run Install Shyft again: it picks up where it left off." }
  Ok "$m downloaded"
}

Say "5/5  Shyft code and test screenshots"
if (Test-Path (Join-Path $ShyftHome ".git")) {
  git -C $ShyftHome pull --ff-only -q
  if ($LASTEXITCODE -eq 0) { Ok "Code updated" } else { Warn "Couldn't update the code; using the copy already here." }
} else {
  git clone -q $RepoUrl $ShyftHome
  if ($LASTEXITCODE -ne 0) { Stop-Shyft "Couldn't download the Shyft code. Check your internet connection and try again." }
  Ok "Code downloaded to your Shyft folder"
}
$zip = Join-Path $PSScriptRoot "shyft_synthetic_set.zip"
if (-not (Test-Path $zip)) { Stop-Shyft "The test screenshots (shyft_synthetic_set.zip) are missing. Did you extract the whole download first?" }
Expand-Archive -Path $zip -DestinationPath $ShyftHome -Force
Push-Location $ShyftHome
& $py dev/use_set.py synthetic | Out-Null
if ($LASTEXITCODE -ne 0) { Pop-Location; Stop-Shyft "Couldn't switch Shyft to the test screenshots." }
Ok "91 made-up test screenshots ready"

Write-Host "    Running Shyft's own checks (about a minute)..."
& $py -m unittest @Tests *> install_check.txt
if ($LASTEXITCODE -eq 0) { Ok "All checks passed" } else { Warn "Some checks failed. That's still useful: the details are in Shyft\install_check.txt" }
Pop-Location

Write-Host ""
Write-Host "Shyft is installed." -ForegroundColor Green
Write-Host "Next: double-click '2 Run the Shyft test'."
Wait-Enter "Press Enter to close"
