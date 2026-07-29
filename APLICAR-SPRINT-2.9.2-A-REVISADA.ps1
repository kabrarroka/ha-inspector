$ErrorActionPreference = "Stop"

$PackageRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepositoryRoot = Get-Location

Copy-Item `
    -Path "$PackageRoot\custom_components\ha_inspector\engine\result.py" `
    -Destination "$RepositoryRoot\custom_components\ha_inspector\engine\result.py" `
    -Force

Copy-Item `
    -Path "$PackageRoot\tests\test_rule_execution_result.py" `
    -Destination "$RepositoryRoot\tests\test_rule_execution_result.py" `
    -Force

$OldTest = Join-Path $RepositoryRoot "tests\test_inspection_result.py"
if (Test-Path $OldTest) {
    Remove-Item $OldTest -Force
    Write-Host "Eliminado archivo de pruebas incompatible: $OldTest"
}

Write-Host "Sprint 2.9.2-A revisada aplicado correctamente."
Write-Host "Ejecuta: python -m pytest -q"
