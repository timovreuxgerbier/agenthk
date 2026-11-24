@echo off
title Shyft installer
rem Runs files\install.ps1 (plain text you can read in Notepad).
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0files\install.ps1"
