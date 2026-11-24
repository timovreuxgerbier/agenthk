@echo off
title Shyft test
rem Runs files\run_test.ps1 (plain text you can read in Notepad).
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0files\run_test.ps1"
