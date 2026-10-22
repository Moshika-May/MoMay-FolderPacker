@echo off
cd /d "%~dp0"
for %%F in (organizer_gui.py app.ico app.png) do (
    if not exist "%%F" (
        echo Missing file: %%F
        echo Put organizer_gui.py, app.ico and app.png in this folder: %~dp0
        pause
        exit /b 1
    )
)
echo Installing PyInstaller...
py -m pip install --upgrade pyinstaller || goto :error
echo Building MoMay-FolderPacker.exe...
py -m PyInstaller --onefile --windowed --name MoMay-FolderPacker --icon app.ico --add-data "app.png;." organizer_gui.py || goto :error
echo.
echo Done! Your program is at: %~dp0dist\MoMay-FolderPacker.exe
pause
exit /b 0

:error
echo Build failed. Read the ERROR line above for the reason.
pause
exit /b 1
