$source = "C:\Users\crtve\Desarrollo\ha-inspector\custom_components\ha_inspector"
$destination = "Z:\config\custom_components\ha_inspector"

if (-not (Test-Path $source)) {
    Write-Error "No existe el origen: $source"
    exit 1
}

if (-not (Test-Path "Z:\")) {
    Write-Error "La unidad Z: no está disponible."
    exit 1
}

robocopy $source $destination /MIR /R:2 /W:2

if ($LASTEXITCODE -ge 8) {
    Write-Error "Robocopy terminó con un error. Código: $LASTEXITCODE"
    exit $LASTEXITCODE
}

Write-Host "HA Inspector sincronizado correctamente."