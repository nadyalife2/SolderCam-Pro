@echo off
chcp 65001 >nul
title Triad-Omni Universal Disaster Recovery Center v4.9
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0UNIVERSAL_DISASTER_RECOVERY_VAULT\scripts\master_control.ps1"
pause
