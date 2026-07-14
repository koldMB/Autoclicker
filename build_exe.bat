@echo off
REM Build Windows EXE with PyInstaller
REM Requirements: pyinstaller installed (pip install pyinstaller)











SET SCRIPT_DIR=%~dp0
SET ICON_FLAG=
IF EXIST "%SCRIPT_DIR%logotipasKoldTools.ico" (
  SET ICON_FLAG=--icon "%SCRIPT_DIR%logotipasKoldTools.ico"
) ELSE (
  echo NOTE: No logotipasKoldTools.ico found. If you have an .ico, place it next to this script named logotipasKoldTools.ico to embed it.
)

REM You can remove --noconsole if you want a console window for debugging
pyinstaller --noconsole --onefile %ICON_FLAG% "%SCRIPT_DIR%main.py"
echo.
echo Build finished. Check the "dist" folder for your executable.
echo To create an installer or bundle, consider using tools like Inno Setup or NSIS.
pause