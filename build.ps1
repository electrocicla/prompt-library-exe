#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Build Not-Meta Prompt Library into a Windows .exe.
.DESCRIPTION
    1. Creates a virtual environment (if not present)
    2. Installs dependencies
    3. Generates the app icon
    4. Runs PyInstaller to produce dist/PromptLibrary.exe
.EXAMPLE
    .\build.ps1
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ROOT   = $PSScriptRoot
$VENV   = Join-Path $ROOT ".venv"
$PYTHON = if (Test-Path "$VENV\Scripts\python.exe") { "$VENV\Scripts\python.exe" } else { "python" }
$PIP    = if (Test-Path "$VENV\Scripts\pip.exe")    { "$VENV\Scripts\pip.exe"    } else { "pip" }

Write-Host "`n══════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Not-Meta Prompt Library – Build Script" -ForegroundColor Cyan
Write-Host "══════════════════════════════════════════`n" -ForegroundColor Cyan

# ── 1. Virtual environment ─────────────────────────────────────────────────
if (-not (Test-Path $VENV)) {
    Write-Host "[1/4] Creating virtual environment…" -ForegroundColor Green
    python -m venv $VENV
} else {
    Write-Host "[1/4] Virtual environment exists – skipping creation." -ForegroundColor DarkGreen
}

# ── 2. Install dependencies ───────────────────────────────────────────────
Write-Host "[2/4] Installing dependencies…" -ForegroundColor Green
& $PIP install --upgrade pip --quiet
& $PIP install -r "$ROOT\requirements.txt" --quiet

# ── 3. Generate icon ──────────────────────────────────────────────────────
Write-Host "[3/4] Generating icon…" -ForegroundColor Green
& $PYTHON "$ROOT\assets\generate_icon.py"

# ── 4. PyInstaller ────────────────────────────────────────────────────────
Write-Host "[4/4] Building executable…" -ForegroundColor Green

$ICO = "$ROOT\assets\icon.ico"
$SRC = "$ROOT\src"

& $PYTHON -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name "PromptLibrary" `
    --icon "$ICO" `
    --add-data "$ROOT\assets;assets" `
    --paths "$SRC" `
    --hidden-import customtkinter `
    --hidden-import PIL `
    --hidden-import PIL.Image `
    --hidden-import PIL.ImageTk `
    "$SRC\main.py"

$EXE = "$ROOT\dist\PromptLibrary.exe"
if (Test-Path $EXE) {
    Write-Host "`n✅  Build complete: $EXE" -ForegroundColor Green
    Write-Host "    Run with: .\dist\PromptLibrary.exe`n" -ForegroundColor Cyan
} else {
    Write-Error "Build failed – exe not found at $EXE"
}
