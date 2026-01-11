@echo off
echo =======================================
echo   ComfyUI Requirements Installation
echo =======================================

REM Current plugin directory
set "PLUGIN_DIR=%cd%"

REM Navigate up to find ComfyUI_windows_portable
set "PORTABLE_DIR=%PLUGIN_DIR%\..\..\.."
for %%i in ("%PORTABLE_DIR%") do set "PORTABLE_DIR=%%~fi"

REM Python embedded location
set "PYTHON_EXE=%PORTABLE_DIR%\python_embeded\python.exe"

REM requirements.txt
set "REQ_FILE=%PLUGIN_DIR%\requirements.txt"

echo Plugin Directory: %PLUGIN_DIR%
echo ComfyUI Portable Root: %PORTABLE_DIR%
echo Python Location: %PYTHON_EXE%
echo Requirements: %REQ_FILE%
echo.

REM Check if python exists
if not exist "%PYTHON_EXE%" (
    echo [ERROR] Cannot find python_embeded\python.exe
    echo Please make sure you are using ComfyUI Portable version
    pause
    exit /b
)

REM Check if requirements.txt exists
if not exist "%REQ_FILE%" (
    echo [ERROR] Cannot find requirements.txt
    pause
    exit /b
)

:INSTALL_RETRY
echo Installing from requirements.txt ...
echo ---------------------------------------
"%PYTHON_EXE%" -m pip install -r "%REQ_FILE%" --no-warn-script-location
set "ERRCODE=%ERRORLEVEL%"
echo ---------------------------------------
echo.

if %ERRCODE% NEQ 0 (
    echo [WARNING] Installation encountered errors
    echo This might be due to network issues or package conflicts
    echo.
    echo Please choose next step:
    echo   1. Retry installation
    echo   2. Skip errors and continue
    echo   3. Exit
    echo.
    set /p USERINPUT=Enter 1/2/3: 

    if "%USERINPUT%"=="1" (
        echo.
        echo ===== Retrying Installation =====
        echo.
        goto INSTALL_RETRY
    )
    if "%USERINPUT%"=="2" (
        echo.
        echo ***** Installation marked as complete *****
        goto END
    )
    if "%USERINPUT%"=="3" (
        echo.
        echo Exiting...
        exit /b
    )

    echo Invalid input, please try again...
    goto INSTALL_RETRY
)

echo.
echo =======================================
echo   Installation completed successfully!
echo =======================================
goto END

:END
echo.
echo Please restart ComfyUI to use the new features.
pause
