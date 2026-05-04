@echo off
setlocal

cd /d %~dp0\..\..
set "BUILD_ERROR="
set "VENV_DIR=.build-venv"
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"

echo [1/5] Checking Python...
python --version
if errorlevel 1 (
    set "BUILD_ERROR=Python is not available."
    goto :fail
)

echo [2/5] Preparing isolated build environment...
if exist %VENV_DIR% rmdir /s /q %VENV_DIR%
python -m venv %VENV_DIR%
if errorlevel 1 (
    set "BUILD_ERROR=Failed to create isolated build virtual environment."
    goto :fail
)

%VENV_PY% -m pip install --upgrade pip
if errorlevel 1 (
    set "BUILD_ERROR=Failed to upgrade pip inside isolated build environment."
    goto :fail
)

%VENV_PY% -m pip install --no-cache-dir -r requirements.txt
if errorlevel 1 (
    set "BUILD_ERROR=Failed to install project dependencies inside isolated build environment."
    goto :fail
)

%VENV_PY% -m pip install --no-cache-dir --force-reinstall PySide6-Fluent-Widgets
if errorlevel 1 (
    set "BUILD_ERROR=Failed to install PySide6-Fluent-Widgets inside isolated build environment."
    goto :fail
)

%VENV_PY% -m pip install --no-cache-dir pyinstaller
if errorlevel 1 (
    set "BUILD_ERROR=Failed to install PyInstaller inside isolated build environment."
    goto :fail
)

echo [3/5] Cleaning previous build...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist release\windows-build-output\FrameMorph-python rmdir /s /q release\windows-build-output\FrameMorph-python
if exist release\windows-build-output\FrameMorph-python-windows-portable.zip del /f /q release\windows-build-output\FrameMorph-python-windows-portable.zip
if not exist release\windows-build-output mkdir release\windows-build-output

echo [4/5] Building Windows portable package...
%VENV_PY% -m PyInstaller release\windows-portable\FrameMorph-python.spec --noconfirm
if errorlevel 1 (
    set "BUILD_ERROR=PyInstaller build failed."
    goto :fail
)

if not exist dist\FrameMorph-python (
    set "BUILD_ERROR=Expected build output not found: dist\FrameMorph-python"
    goto :fail
)

echo [5/5] Copying build output...
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
