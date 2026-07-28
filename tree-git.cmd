@echo off
setlocal

echo =====================================
echo Esportazione struttura del progetto
echo =====================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass ^
 "Get-ChildItem -Recurse | Select-Object FullName | Out-File struttura.txt -Encoding UTF8"

if errorlevel 1 goto :err

git ls-tree -r HEAD --name-only > repository.txt

if errorlevel 1 goto :err

echo.
echo Generati:
echo   struttura.txt
echo   repository.txt
goto :end

:err
echo.
echo Si e verificato un errore.

:end
pause
