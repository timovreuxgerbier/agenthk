# remove.ps1 - started by "3 Remove Shyft.bat". Takes away ONLY what this kit brought (see record.txt):
# the models it downloaded and the Shyft folder it made. Never uninstalls programs by itself.
# Keeps the "Shyft test results" folder.
$ScriptName = "3 Remove"
. (Join-Path $PSScriptRoot "common.ps1")
. (Join-Path $PSScriptRoot "results.ps1")
Clear-Host
Write-Host @"
  Remove Shyft
  ------------
  This removes only what the tester kit brought to your PC:
    - the Rick and Zippy models it downloaded (up to about 11 GB)
    - the Shyft folder it made in your user folder
  Anything that was already on your PC stays. Your 'Shyft test results' folder stays.
  Programs the kit installed are NOT removed automatically: you'll see how to remove them.
"@
Wait-Enter "Press Enter to remove (or close this window to cancel)"
$failed = $false

Say "Models"
$ol = Find-Ollama; $mine = @(Get-Record "model")
if (-not $ol) { Ok "Ollama isn't installed, so there are no models to remove" }
else {
  if (-not (Test-OllamaUp)) { Start-OllamaApp; Wait-Ollama | Out-Null }
  foreach ($m in $Models.Keys) {
    $here = Test-Model $ol $m
    if ($mine -contains $m) {
      if ($here) {
        & $ol rm $m | Out-Null
        if ($LASTEXITCODE -eq 0) { Ok "Removed $m" } else { Warn "Couldn't remove $m"; Note "Couldn't remove $m"; $failed = $true }
      } else {
        Warn "$m was only partly downloaded, so it can't be removed by name and may still use some space."
        Write-Host "    To clear it: run '1 Install Shyft' to finish the download, then run '3 Remove Shyft' again."
        Note "Partial download of $m left on the PC"; $failed = $true    # keep the kit's notes so the next Remove still knows it's ours
      }
    } elseif ($here) { Ok "Left ${m}: it was already on this PC before the kit" }
  }
}

Say "Shyft folder"
if (@(Get-Record "shyft_folder").Count -gt 0) {
  if (Test-Path $ShyftHome) {
    try { Remove-Item -Recurse -Force $ShyftHome -ErrorAction Stop; Ok "Removed the Shyft folder" }
    catch { Warn "Couldn't remove the Shyft folder (is a file in it open?)"; Note "Couldn't remove Shyft folder"; $failed = $true }
  } else { Ok "The Shyft folder is already gone" }
} elseif (Test-Path $ShyftHome) { Ok "Left the Shyft folder alone: this kit didn't make it" }

Say "What stays installed"
$progs = @(Get-Record "program")
if ($progs.Count -eq 0) { Ok "The kit didn't install any programs" }
else {
  Write-Host "    The kit installed these programs. Remove them yourself if you don't want them:"
  foreach ($p in $progs) { Write-Host "      - $p" }
}
if ($ol) { Write-Host "    Ollama keeps a few small settings and logs in your user folder until you uninstall it." }

if (-not $failed) { Remove-Item -Recurse -Force $KitDir -ErrorAction SilentlyContinue; Ok "Done. The kit's own notes are removed too." }
else { Warn "Some things couldn't be removed. Run '3 Remove Shyft' again later; the kit kept its notes for that." }
Wait-Enter "Press Enter to close"
