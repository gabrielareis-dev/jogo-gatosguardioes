@echo off
setlocal
cd /d "%~dp0"

echo Instalando dependencias do projeto...
python -m pip install -r requirements.txt
if errorlevel 1 goto erro

echo Gerando executavel portatil para Windows...
python -m PyInstaller --noconfirm --clean --windowed --onefile --name GatosGuardioes --workpath build_repair --distpath dist_repair main.py
if errorlevel 1 goto erro

echo Preparando somente o executavel e os assets...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference = 'Stop'; if (Test-Path 'package_windows') { Remove-Item 'package_windows' -Recurse -Force }; New-Item -ItemType Directory -Path 'package_windows\assets\sprites','package_windows\assets\backgrounds' -Force | Out-Null; Copy-Item 'dist_repair\GatosGuardioes.exe' 'package_windows\GatosGuardioes.exe'; Copy-Item 'assets\music' 'package_windows\assets\music' -Recurse; Copy-Item 'assets\sounds' 'package_windows\assets\sounds' -Recurse; Copy-Item 'assets\sprites\*.png' 'package_windows\assets\sprites'; Copy-Item 'assets\backgrounds\game_background.jpg' 'package_windows\assets\backgrounds'; if (Test-Path 'GatosGuardioes-Windows.new.zip') { Remove-Item 'GatosGuardioes-Windows.new.zip' -Force }; Compress-Archive -Path 'package_windows\GatosGuardioes.exe','package_windows\assets' -DestinationPath 'GatosGuardioes-Windows.new.zip' -Force; if (Test-Path 'GatosGuardioes-Windows.zip') { Remove-Item 'GatosGuardioes-Windows.zip' -Force }; Move-Item 'GatosGuardioes-Windows.new.zip' 'GatosGuardioes-Windows.zip'; Remove-Item 'package_windows' -Recurse -Force"
if errorlevel 1 goto erro

echo.
echo Pronto: GatosGuardioes-Windows.zip
echo O ZIP contem GatosGuardioes.exe e a pasta assets.
pause
exit /b 0

:erro
echo.
echo O build falhou. Confira a mensagem acima e verifique se Python esta instalado.
pause
exit /b 1
