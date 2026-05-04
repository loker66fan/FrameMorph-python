@echo off
setlocal EnableExtensions EnableDelayedExpansion

cd /d %~dp0\..\..
set "BUILD_ERROR="
set "BUILD_REQUIREMENTS=release\windows-portable\requirements-windows-build.txt"
set "WHEELHOUSE_DIR=release\windows-portable\wheelhouse"
set "VENV_DIR=%TEMP%\FrameMorph-python-build-venv-%RANDOM%%RANDOM%"
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"
set "ACTIVE_PYTHON="
set "ACTIVE_PYTHON_ARGS="

echo [1/6] Resolving Python runtime...
if defined FRAME_MORPH_PYTHON (
    if exist "%FRAME_MORPH_PYTHON%" (
        set "ACTIVE_PYTHON="%FRAME_MORPH_PYTHON%""
        set "ACTIVE_PYTHON_ARGS="
        echo Using FRAME_MORPH_PYTHON override: %FRAME_MORPH_PYTHON%
    ) else (
        set "BUILD_ERROR=FRAME_MORPH_PYTHON was set, but the file does not exist: %FRAME_MORPH_PYTHON%"
        goto :fail
    )
)

if not defined ACTIVE_PYTHON (
    where py >nul 2>nul
    if not errorlevel 1 (
        py -3 -c "import sys" >nul 2>nul
        if not errorlevel 1 (
            set "ACTIVE_PYTHON=py"
            set "ACTIVE_PYTHON_ARGS=-3"
            echo Using py launcher with -3.
        )
    )
)

if not defined ACTIVE_PYTHON (
    where py >nul 2>nul
    if not errorlevel 1 (
        py -c "import sys" >nul 2>nul
        if not errorlevel 1 (
            set "ACTIVE_PYTHON=py"
            set "ACTIVE_PYTHON_ARGS="
            echo Using default py launcher.
        )
    )
)

if not defined ACTIVE_PYTHON (
    where python >nul 2>nul
    if not errorlevel 1 (
        set "SYSTEM_PYTHON_PATH="
        for /f "delims=" %%I in ('where python 2^>nul') do (
            echo %%I | find /i "\WindowsApps\python.exe" >nul
            if errorlevel 1 if not defined SYSTEM_PYTHON_PATH set "SYSTEM_PYTHON_PATH=%%I"
        )
        if defined SYSTEM_PYTHON_PATH (
            set "ACTIVE_PYTHON="!SYSTEM_PYTHON_PATH!""
            set "ACTIVE_PYTHON_ARGS="
            echo Using python.exe on PATH: !SYSTEM_PYTHON_PATH!
        ) else (
            echo Ignoring WindowsApps python.exe alias on PATH.
        )
    )
)

if not defined ACTIVE_PYTHON (
    set "BUILD_ERROR=No usable Python interpreter was found. Set FRAME_MORPH_PYTHON to a real python.exe, or ensure py/python is available."
    goto :fail
)

if not exist "%BUILD_REQUIREMENTS%" (
    set "BUILD_ERROR=Missing build requirements file: %BUILD_REQUIREMENTS%"
    goto :fail
)

echo Using Python command: %ACTIVE_PYTHON% %ACTIVE_PYTHON_ARGS%

echo [2/6] Preparing isolated build environment...
if exist "%VENV_DIR%" rmdir /s /q "%VENV_DIR%"
%ACTIVE_PYTHON% %ACTIVE_PYTHON_ARGS% -m venv --clear --copies "%VENV_DIR%"
if errorlevel 1 (
    set "BUILD_ERROR=Failed to create isolated build virtual environment. If needed, set FRAME_MORPH_PYTHON to a real python.exe."
    goto :fail
)
if not exist "%VENV_PY%" (
    set "BUILD_ERROR=Virtual environment was created, but %VENV_PY% was not found."
    goto :fail
)
"%VENV_PY%" -c "import sys; sys.exit(0)" >nul 2>nul
if errorlevel 1 (
    set "BUILD_ERROR=Created virtual environment is not runnable."
    goto :fail
)

echo [3/6] Installing build dependencies...
dir /b "%WHEELHOUSE_DIR%\*.whl" >nul 2>nul
if not errorlevel 1 (
    echo Found local wheelhouse. Installing dependencies without network access...
    "%VENV_PY%" -m pip install --no-index --find-links "%WHEELHOUSE_DIR%" -r "%BUILD_REQUIREMENTS%"
    if errorlevel 1 (
        set "BUILD_ERROR=Failed to install build dependencies from local wheelhouse."
        goto :fail
    )
) else (
    echo No local wheelhouse found under %WHEELHOUSE_DIR%.
    echo Falling back to online dependency installation...
    "%VENV_PY%" -m pip install --no-cache-dir -r "%BUILD_REQUIREMENTS%"
    if errorlevel 1 (
        set "BUILD_ERROR=Failed to install build dependencies from the network."
        goto :fail
    )
)

echo [4/6] Cleaning previous build...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist release\windows-build-output\FrameMorph-python rmdir /s /q release\windows-build-output\FrameMorph-python
if exist release\windows-build-output\FrameMorph-python-windows-portable.zip del /f /q release\windows-build-output\FrameMorph-python-windows-portable.zip
if not exist release\windows-build-output mkdir release\windows-build-output

echo [5/6] Building Windows portable package...
"%VENV_PY%" -m PyInstaller release\windows-portable\FrameMorph-python.spec --noconfirm
if errorlevel 1 (
    set "BUILD_ERROR=PyInstaller build failed."
    goto :fail
)

if not exist dist\FrameMorph-python (
    set "BUILD_ERROR=Expected build output not found: dist\FrameMorph-python"
    goto :fail
)

echo [6/6] Copying build output...
mkdir release\windows-build-output\FrameMorph-python
robocopy dist\FrameMorph-python release\windows-build-output\FrameMorph-python /E
if errorlevel 8 (
    set "BUILD_ERROR=Failed to copy portable build into release\windows-build-output\FrameMorph-python"
    goto :fail
)

if not exist release\windows-build-output\FrameMorph-python\FrameMorph-python.exe (
    set "BUILD_ERROR=Portable executable not found after copy: release\windows-build-output\FrameMorph-python\FrameMorph-python.exe"
    goto :fail
)

powershell -NoProfile -Command ^
    "Compress-Archive -Path 'release/windows-build-output/FrameMorph-python/*' -DestinationPath 'release/windows-build-output/FrameMorph-python-windows-portable.zip' -Force"
if errorlevel 1 (
    set "BUILD_ERROR=Failed to create zip package."
    goto :fail
)

goto :success

:success
echo.
echo ==========================================
echo BUILD SUCCESS
echo ==========================================
echo Windows portable package has been created.
echo.
echo Output folder 1: dist\FrameMorph-python
echo Output folder 2: release\windows-build-output\FrameMorph-python
echo Output zip    : release\windows-build-output\FrameMorph-python-windows-portable.zip
echo Build venv    : %VENV_DIR%
echo Build deps    : %BUILD_REQUIREMENTS%
echo Wheelhouse    : %WHEELHOUSE_DIR%
echo Python cmd    : %ACTIVE_PYTHON% %ACTIVE_PYTHON_ARGS%
echo.
echo Important: do not copy only FrameMorph-python.exe by itself.
echo Copy the whole FrameMorph-python folder or use the generated zip package.
echo You can copy the folder or zip to another Windows device.
echo ==========================================
echo.
pause
endlocal
exit /b 0

:fail
echo.
echo ==========================================
echo BUILD FAILED
echo ==========================================
echo Reason:
echo %BUILD_ERROR%
echo.
echo Please check the log above for more details.
echo ==========================================
echo.
pause
endlocal
exit /b 1
