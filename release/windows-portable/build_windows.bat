@echo off
setlocal EnableExtensions EnableDelayedExpansion

cd /d %~dp0\..\..
set "BUILD_ERROR="
set "BUILD_REQUIREMENTS=release\windows-portable\requirements-windows-build.txt"
set "WHEELHOUSE_DIR=release\windows-portable\wheelhouse"
set "EXPECTED_PYTHON_VERSION=3.11"
set "BOOTSTRAP_INSTALLER=release\windows-portable\python-installer\python-3.11.9-amd64.exe"
set "BOOTSTRAP_RUNTIME_DIR=release\windows-portable\python-runtime"
set "BOOTSTRAP_INSTALL_LOG=release\windows-portable\python-runtime-install.log"
set "BOOTSTRAP_RUNTIME_ABS=%CD%\release\windows-portable\python-runtime"
set "BOOTSTRAP_INSTALLER_ABS=%CD%\release\windows-portable\python-installer\python-3.11.9-amd64.exe"
set "PYTHON_CHECK_CMD=import sys; sys.exit(0 if sys.version_info[:2] == (3, 11) else 1)"
set "VENV_DIR=%TEMP%\FrameMorph-python-build-venv-%RANDOM%%RANDOM%"
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"
set "ACTIVE_PYTHON="
set "ACTIVE_PYTHON_ARGS="
set "ACTIVE_PYTHON_VERSION="

echo [1/7] Resolving Python runtime...
where py >nul 2>nul
if not errorlevel 1 (
    py -%EXPECTED_PYTHON_VERSION% -c "%PYTHON_CHECK_CMD%" >nul 2>nul
    if not errorlevel 1 (
        set "ACTIVE_PYTHON=py"
        set "ACTIVE_PYTHON_ARGS=-%EXPECTED_PYTHON_VERSION%"
        set "ACTIVE_PYTHON_VERSION=%EXPECTED_PYTHON_VERSION%"
        echo Detected Python via py launcher.
    )
)

if not defined ACTIVE_PYTHON (
    echo py launcher did not provide Python %EXPECTED_PYTHON_VERSION%. Checking python.exe on PATH...
)

where python >nul 2>nul
if not errorlevel 1 if not defined ACTIVE_PYTHON (
    set "SYSTEM_PYTHON_PATH="
    for /f "delims=" %%I in ('where python 2^>nul') do if not defined SYSTEM_PYTHON_PATH set "SYSTEM_PYTHON_PATH=%%I"
    "!SYSTEM_PYTHON_PATH!" -c "%PYTHON_CHECK_CMD%" >nul 2>nul
    if not errorlevel 1 (
        set "ACTIVE_PYTHON="!SYSTEM_PYTHON_PATH!""
        set "ACTIVE_PYTHON_ARGS="
        set "ACTIVE_PYTHON_VERSION=%EXPECTED_PYTHON_VERSION%"
        echo Detected Python via python.exe on PATH: !SYSTEM_PYTHON_PATH!
    )
)

if not defined ACTIVE_PYTHON (
    echo PATH lookup did not provide Python %EXPECTED_PYTHON_VERSION%. Checking Python runtime in project directory...
    if exist "%BOOTSTRAP_RUNTIME_ABS%\python.exe" (
        "%BOOTSTRAP_RUNTIME_ABS%\python.exe" -c "%PYTHON_CHECK_CMD%" >nul 2>nul
        if not errorlevel 1 (
            set "ACTIVE_PYTHON="%BOOTSTRAP_RUNTIME_ABS%\python.exe""
            set "ACTIVE_PYTHON_ARGS="
            set "ACTIVE_PYTHON_VERSION=%EXPECTED_PYTHON_VERSION%"
            echo Reusing bundled local Python runtime.
        )
    )
)

if not defined ACTIVE_PYTHON (
    echo Local runtime not found. Checking Windows registry for Python %EXPECTED_PYTHON_VERSION%...
    set "REGISTRY_PATH="
    for /f "tokens=2,*" %%A in ('reg query "HKCU\Software\Python\PythonCore\%EXPECTED_PYTHON_VERSION%\InstallPath" /ve 2^>nul ^| find "REG_SZ"') do set "REGISTRY_PATH=%%B"
    if defined REGISTRY_PATH if exist "!REGISTRY_PATH!python.exe" (
        "!REGISTRY_PATH!python.exe" -c "%PYTHON_CHECK_CMD%" >nul 2>nul
        if not errorlevel 1 (
            set "ACTIVE_PYTHON="!REGISTRY_PATH!python.exe""
            set "ACTIVE_PYTHON_ARGS="
            set "ACTIVE_PYTHON_VERSION=%EXPECTED_PYTHON_VERSION%"
            echo Detected Python via registry: HKCU\Software\Python\PythonCore\%EXPECTED_PYTHON_VERSION%\InstallPath
        )
    )
)

if not defined ACTIVE_PYTHON (
    set "REGISTRY_PATH="
    for /f "tokens=2,*" %%A in ('reg query "HKLM\Software\Python\PythonCore\%EXPECTED_PYTHON_VERSION%\InstallPath" /ve 2^>nul ^| find "REG_SZ"') do set "REGISTRY_PATH=%%B"
    if defined REGISTRY_PATH if exist "!REGISTRY_PATH!python.exe" (
        "!REGISTRY_PATH!python.exe" -c "%PYTHON_CHECK_CMD%" >nul 2>nul
        if not errorlevel 1 (
            set "ACTIVE_PYTHON="!REGISTRY_PATH!python.exe""
            set "ACTIVE_PYTHON_ARGS="
            set "ACTIVE_PYTHON_VERSION=%EXPECTED_PYTHON_VERSION%"
            echo Detected Python via registry: HKLM\Software\Python\PythonCore\%EXPECTED_PYTHON_VERSION%\InstallPath
        )
    )
)

if not defined ACTIVE_PYTHON (
    set "REGISTRY_PATH="
    for /f "tokens=2,*" %%A in ('reg query "HKLM\Software\WOW6432Node\Python\PythonCore\%EXPECTED_PYTHON_VERSION%\InstallPath" /ve 2^>nul ^| find "REG_SZ"') do set "REGISTRY_PATH=%%B"
    if defined REGISTRY_PATH if exist "!REGISTRY_PATH!python.exe" (
        "!REGISTRY_PATH!python.exe" -c "%PYTHON_CHECK_CMD%" >nul 2>nul
        if not errorlevel 1 (
            set "ACTIVE_PYTHON="!REGISTRY_PATH!python.exe""
            set "ACTIVE_PYTHON_ARGS="
            set "ACTIVE_PYTHON_VERSION=%EXPECTED_PYTHON_VERSION%"
            echo Detected Python via registry: HKLM\Software\WOW6432Node\Python\PythonCore\%EXPECTED_PYTHON_VERSION%\InstallPath
        )
    )
)

if not defined ACTIVE_PYTHON (
    if not exist "%BOOTSTRAP_INSTALLER%" (
        set "BUILD_ERROR=Python 3.11 was not found, and no bundled installer exists at %BOOTSTRAP_INSTALLER%."
        goto :fail
    )
    echo No usable Python %EXPECTED_PYTHON_VERSION% found. Installing bundled local runtime...
    echo Installer: %BOOTSTRAP_INSTALLER%
    echo Install log: %BOOTSTRAP_INSTALL_LOG%
    echo A Python setup progress window should appear. This step may take a few minutes on slower machines.
    if exist "%BOOTSTRAP_RUNTIME_ABS%" rmdir /s /q "%BOOTSTRAP_RUNTIME_ABS%"
    if exist "%BOOTSTRAP_INSTALL_LOG%" del /f /q "%BOOTSTRAP_INSTALL_LOG%"
    start /wait "" "%BOOTSTRAP_INSTALLER_ABS%" /passive /log "%CD%\%BOOTSTRAP_INSTALL_LOG%" InstallAllUsers=0 "TargetDir=%BOOTSTRAP_RUNTIME_ABS%" Include_pip=1 Include_exe=1 Include_lib=1 Include_dev=1 Include_launcher=0 AssociateFiles=0 Shortcuts=0 PrependPath=0 Include_test=0 Include_tcltk=0 Include_doc=0
    if errorlevel 1 (
        set "BUILD_ERROR=Failed to install bundled Python runtime. See %BOOTSTRAP_INSTALL_LOG%."
        goto :fail
    )

    set "FOUND_BOOTSTRAP_PYTHON="
    if exist "%BOOTSTRAP_RUNTIME_ABS%\python.exe" (
        set "FOUND_BOOTSTRAP_PYTHON=%BOOTSTRAP_RUNTIME_ABS%\python.exe"
    )
    if not defined FOUND_BOOTSTRAP_PYTHON (
        for /r "%BOOTSTRAP_RUNTIME_ABS%" %%F in (python.exe) do (
            if not defined FOUND_BOOTSTRAP_PYTHON set "FOUND_BOOTSTRAP_PYTHON=%%F"
        )
    )
    if not defined FOUND_BOOTSTRAP_PYTHON (
        if exist "%LocalAppData%\Programs\Python\Python311\python.exe" (
            set "FOUND_BOOTSTRAP_PYTHON=%LocalAppData%\Programs\Python\Python311\python.exe"
        )
    )
    if not defined FOUND_BOOTSTRAP_PYTHON (
        where py >nul 2>nul
        if not errorlevel 1 (
            py -%EXPECTED_PYTHON_VERSION% -c "%PYTHON_CHECK_CMD%" >nul 2>nul
            if not errorlevel 1 (
                set "ACTIVE_PYTHON=py"
                set "ACTIVE_PYTHON_ARGS=-%EXPECTED_PYTHON_VERSION%"
                set "ACTIVE_PYTHON_VERSION=%EXPECTED_PYTHON_VERSION%"
                echo Installed bundled Python runtime is now reachable via py launcher.
            )
        )
    )
    if defined ACTIVE_PYTHON goto :python_ready
    if not defined FOUND_BOOTSTRAP_PYTHON (
        set "BUILD_ERROR=Bundled Python installer completed, but python.exe was not found under %BOOTSTRAP_RUNTIME_DIR% or %%LocalAppData%%\\Programs\\Python\\Python311. See %BOOTSTRAP_INSTALL_LOG%."
        goto :fail
    )

    "!FOUND_BOOTSTRAP_PYTHON!" -c "%PYTHON_CHECK_CMD%" >nul 2>nul
    if errorlevel 1 (
        echo Installed Python candidate: !FOUND_BOOTSTRAP_PYTHON!
        set "BUILD_ERROR=Bundled Python runtime exists but failed the Python 3.11 validation check. See %BOOTSTRAP_INSTALL_LOG%."
        goto :fail
    )
    set "ACTIVE_PYTHON="!FOUND_BOOTSTRAP_PYTHON!""
    set "ACTIVE_PYTHON_ARGS="
    set "ACTIVE_PYTHON_VERSION=%EXPECTED_PYTHON_VERSION%"
    echo Installed bundled Python runtime: !FOUND_BOOTSTRAP_PYTHON!
)

:python_ready
if not exist %BUILD_REQUIREMENTS% (
    set "BUILD_ERROR=Missing build requirements file: %BUILD_REQUIREMENTS%"
    goto :fail
)

echo Using Python: %ACTIVE_PYTHON%
echo Python version: %ACTIVE_PYTHON_VERSION%

echo [2/7] Preparing isolated build environment...
if exist "%VENV_DIR%" rmdir /s /q "%VENV_DIR%"
%ACTIVE_PYTHON% %ACTIVE_PYTHON_ARGS% -m venv --clear --copies "%VENV_DIR%"
if errorlevel 1 (
    set "BUILD_ERROR=Failed to create isolated build virtual environment."
    goto :fail
)
if not exist "%VENV_PY%" (
    set "BUILD_ERROR=Virtual environment was created, but %VENV_PY% was not found."
    goto :fail
)
"%VENV_PY%" -c "import sys; sys.exit(0)" >nul 2>nul
if errorlevel 1 (
    set "BUILD_ERROR=Created virtual environment is not runnable. It may be referencing a stale Python launcher."
    goto :fail
)

echo [3/7] Installing build dependencies...
dir /b %WHEELHOUSE_DIR%\*.whl >nul 2>nul
if not errorlevel 1 (
    echo Found local wheelhouse. Installing dependencies without network access...
    %VENV_PY% -m pip install --no-index --find-links %WHEELHOUSE_DIR% -r %BUILD_REQUIREMENTS%
    if errorlevel 1 (
        set "BUILD_ERROR=Failed to install build dependencies from local wheelhouse."
        goto :fail
    )
) else (
    echo No local wheelhouse found under %WHEELHOUSE_DIR%.
    echo Falling back to online dependency installation...
    %VENV_PY% -m pip install --no-cache-dir -r %BUILD_REQUIREMENTS%
    if errorlevel 1 (
        set "BUILD_ERROR=Failed to install build dependencies from the network."
        goto :fail
    )
)

echo [4/7] Cleaning previous build...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist release\windows-build-output\FrameMorph-python rmdir /s /q release\windows-build-output\FrameMorph-python
if exist release\windows-build-output\FrameMorph-python-windows-portable.zip del /f /q release\windows-build-output\FrameMorph-python-windows-portable.zip
if not exist release\windows-build-output mkdir release\windows-build-output

echo [5/7] Building Windows portable package...
%VENV_PY% -m PyInstaller release\windows-portable\FrameMorph-python.spec --noconfirm
if errorlevel 1 (
    set "BUILD_ERROR=PyInstaller build failed."
    goto :fail
)

if not exist dist\FrameMorph-python (
    set "BUILD_ERROR=Expected build output not found: dist\FrameMorph-python"
    goto :fail
)

echo [6/7] Copying build output...
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

echo [7/7] Finalizing build...

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
echo Python       : %ACTIVE_PYTHON_VERSION%
echo Runtime dir   : %BOOTSTRAP_RUNTIME_DIR%
echo Install log   : %BOOTSTRAP_INSTALL_LOG%
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
