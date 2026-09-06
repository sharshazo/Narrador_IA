@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Narrador_IA - Instalador
cd /d "%~dp0"

echo ============================================================
echo   Narrador_IA para LOTRO - Instalador
echo ============================================================
echo.
echo Esto va a:
echo   1. Buscar Python en tu PC.
echo   2. Crear un entorno propio para Narrador_IA (no toca tu
echo      instalacion de Python general).
echo   3. Instalar las librerias necesarias.
echo   4. Preguntarte si queres que arranque solo cada vez que
echo      abras LOTRO (recomendado).
echo.
echo No hace falta que sepas nada de Python para esto -- solo
echo apretar Enter cuando se te pida.
echo.
pause

echo.
echo ------------------------------------------------------------
echo Paso 1/4: buscando Python...
echo ------------------------------------------------------------
set PYLAUNCHER=
py -3 --version >nul 2>&1
if not errorlevel 1 (
    set PYLAUNCHER=py -3
    goto :python_found
)
python --version >nul 2>&1
if not errorlevel 1 (
    set PYLAUNCHER=python
    goto :python_found
)

echo.
echo No se encontro Python en esta PC -- se va a descargar e instalar
echo solo, directo desde python.org (el sitio oficial). Esto necesita
echo internet y puede tardar un par de minutos.
echo.
set "PY_INSTALLER_URL=https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe"
set "PY_INSTALLER_FILE=%TEMP%\python-installer-questsync.exe"
set "PY_INSTALL_DIR=%LOCALAPPDATA%\Programs\Python\Python312"

echo Descargando Python 3.12 ^(~25 MB^)...
powershell -NoProfile -Command "try { Invoke-WebRequest -Uri '%PY_INSTALLER_URL%' -OutFile '%PY_INSTALLER_FILE%' -UseBasicParsing; exit 0 } catch { Write-Host $_.Exception.Message; exit 1 }"
if errorlevel 1 (
    echo.
    echo ERROR: no se pudo descargar Python ^(revisa tu conexion a
    echo internet^). Como alternativa, instalalo a mano desde
    echo https://www.python.org/downloads/ ^(tildando "Add python.exe
    echo to PATH"^) y volve a correr este archivo.
    pause
    exit /b 1
)

echo Instalando Python ^(silencioso, sin ventanas, no hace falta que
echo hagas nada^)...
"%PY_INSTALLER_FILE%" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0
del "%PY_INSTALLER_FILE%" >nul 2>&1

if not exist "%PY_INSTALL_DIR%\python.exe" (
    echo.
    echo ERROR: la instalacion de Python no termino como se esperaba.
    echo Instalalo a mano desde https://www.python.org/downloads/
    echo ^(tildando "Add python.exe to PATH"^) y volve a correr este
    echo archivo.
    pause
    exit /b 1
)

REM PATH recien se actualiza para ventanas NUEVAS de cmd -- esta misma
REM ventana no lo ve todavia aunque el instalador ya lo haya escrito en
REM el registro. Se usa la ruta completa conocida del instalador oficial
REM en vez de esperar a que "py"/"python" aparezcan solos, asi el resto
REM de ESTE mismo script ya puede seguir sin pedirle a nadie que lo
REM cierre y lo vuelva a abrir.
set PYLAUNCHER="%PY_INSTALL_DIR%\python.exe"
echo.
echo Python instalado correctamente.
echo.
goto :python_found

:python_found
for /f "tokens=2" %%v in ('%PYLAUNCHER% --version 2^>^&1') do set PYVER=%%v
echo Encontrado: Python %PYVER% (%PYLAUNCHER%)
echo.

echo ------------------------------------------------------------
echo Paso 2/4: preparando el entorno de Narrador_IA...
echo ------------------------------------------------------------
if exist ".venv\Scripts\python.exe" (
    echo Ya existe un entorno instalado -- se reutiliza y se actualiza.
) else (
    echo Creando entorno nuevo en ".venv" ^(puede tardar un minuto^)...
    %PYLAUNCHER% -m venv ".venv"
    if errorlevel 1 (
        echo.
        echo ERROR: no se pudo crear el entorno virtual.
        pause
        exit /b 1
    )
)
echo.

echo ------------------------------------------------------------
echo Paso 3/4: instalando librerias necesarias (requiere internet)...
echo ------------------------------------------------------------
".venv\Scripts\python.exe" -m pip install --upgrade pip --quiet
".venv\Scripts\python.exe" -m pip install -r "requirements.txt"
if errorlevel 1 (
    echo.
    echo ERROR: fallo la instalacion de librerias. Revisa el mensaje
    echo de arriba -- lo mas comun es no tener conexion a internet.
    pause
    exit /b 1
)
echo.
echo Listo -- librerias instaladas correctamente.
echo.

echo ------------------------------------------------------------
echo Paso 4/4: arranque automatico
echo ------------------------------------------------------------
echo Si activas esto, Narrador_IA se va a abrir SOLO cada vez que
echo abras LOTRO, y se va a cerrar solo cuando cierres el juego --
echo no vas a tener que acordarte de arrancarlo a mano.
echo.
set /p AUTOSTART="Activar arranque automatico? (S/N): "
if /i "%AUTOSTART%"=="S" (
    set "STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
    set "STARTUP_FILE=!STARTUP_DIR!\Narrador_IA_Vigia.bat"
    (
        echo @echo off
        echo cd /d "%~dp0"
        echo start "" ".venv\Scripts\pythonw.exe" "watcher.py"
    ) > "!STARTUP_FILE!"
    echo.
    echo Listo -- Narrador_IA va a arrancar solo la proxima vez que
    echo abras LOTRO ^(no hace falta reiniciar Windows^).
    echo.
    echo Iniciando el vigia ahora mismo para esta sesion...
    start "" ".venv\Scripts\pythonw.exe" "watcher.py"
) else (
    echo.
    echo Arranque automatico NO activado. Para narrar, vas a tener
    echo que abrir "run_narrador.bat" a mano cada vez que quieras
    echo escuchar la narracion ^(con LOTRO ya abierto^).
)

echo.
echo ============================================================
echo   Instalacion terminada
echo ============================================================
echo.
echo Recorda: los addons de LOTRO (QuestSync y LOTRO_Chat_Narrator)
echo son OTRA carpeta aparte -- si todavia no los copiaste dentro de
echo tu carpeta "Documentos\The Lord of the Rings Online\Plugins\",
echo hacelo ahora (ver LEEME_PRIMERO.txt en la carpeta de arriba).
echo.
pause
exit /b 0
