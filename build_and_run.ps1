pyinstaller --clean --noconfirm `
    --distpath C:\Users\pc\pbd\bin `
    --workpath build `
    pbd.spec

if ($LASTEXITCODE -ne 0) {
    Write-Host "Build failed."
    exit $LASTEXITCODE
}

$choice = Read-Host "Build completed. Run PBD now? [Y/N]"

if ($choice -eq "Y") {
    & C:\Users\pc\pbd\bin\pbd.exe
}