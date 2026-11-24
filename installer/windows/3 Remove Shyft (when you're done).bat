@echo off
title Remove Shyft
rem Runs files\remove.ps1 (plain text you can read in Notepad).
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0files\remove.ps1"
