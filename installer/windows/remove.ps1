# remove.ps1 - started by "3 Remove Shyft.bat". Gives back the space: deletes the Shyft folder and
# the two models (about 17 GB). Keeps the Ollama app and the "Shyft test results" folder.
. (Join-Path $PSScriptRoot "common.ps1")
Clear-Host
Write-Host @"
  Remove Shyft
  ------------
  This deletes:
    - the Shyft folder in your user folder (code and made-up test screenshots)
    - Rick's and Zippy's models (about 17 GB)
  It keeps the Ollama app and the "Shyft test results" folder on your Desktop.
"@
Wait-Enter "Press Enter to remove Shyft (or close this window to cancel)"

$ol = Find-Ollama
if ($ol) {
  if (-not (Test-OllamaUp)) { Start-OllamaApp; Wait-Ollama | Out-Null }
  foreach ($m in $Models) {
    if (Test-Model $ol $m) { & $ol rm $m | Out-Null; if ($LASTEXITCODE -eq 0) { Ok "Removed $m" } else { Warn "Couldn't remove $m" } }
  }
}
if (Test-Path $ShyftHome) { Remove-Item -Recurse -Force $ShyftHome; Ok "Removed the Shyft folder" }
Write-Host ""
Write-Host "Done. To remove Ollama too: Settings > Apps > Installed apps > Ollama > Uninstall."
Wait-Enter "Press Enter to close"
