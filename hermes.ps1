param()

$ErrorActionPreference = "Stop"

$launcher = "D:\code\onto\setup\start-hermes-ontology.ps1"

if (-not (Test-Path $launcher)) {
    throw "Missing launcher script: $launcher"
}

powershell -ExecutionPolicy Bypass -File $launcher
