@echo off
echo ====================================
echo  AOEngine Tools - Cache Clearer
echo ====================================
echo.
echo Clearing Python bytecode cache...
echo.

REM Delete all __pycache__ directories
for /d /r %%d in (__pycache__) do (
    if exist "%%d" (
        echo Removing: %%d
        rd /s /q "%%d"
    )
)

REM Delete all .pyc files
echo.
echo Deleting .pyc files...
del /s /q *.pyc >nul 2>&1

echo.
echo ====================================
echo  Cache cleared successfully!
echo ====================================
echo.
pause
