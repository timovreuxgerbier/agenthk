@echo off
title Remove Shyft
rem Runs files\remove.ps1 (plain text you can read in Notepad).
if not exist "%~dp0files\remove.ps1" (
  echo.
  echo   This button was started from inside the zip, so it can't find the rest of the kit.
  echo   Please unzip first: right-click the zip, choose "Extract All", then "Extract".
  echo   Then open the new folder and double-click this button again.
  echo.
  pause
  exit /b
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0files\remove.ps1"
