REM # Author: Miguel Marina <karel.capek.robotics@gmail.com>
REM # SPDX-License-Identifier: GPL-3.0-or-later
REM #
REM # Copyright (C) 2025 Capek System Safety & Robotic Solutions
REM #
REM # This program is free software: you can redistribute it and/or modify
REM # it under the terms of the GNU General Public License as published by
REM # the Free Software Foundation, either version 3 of the License, or
REM # (at your option) any later version.
REM #
REM # This program is distributed in the hope that it will be useful,
REM # but WITHOUT ANY WARRANTY; without even the implied warranty of
REM # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
REM # GNU General Public License for more details.
REM #
REM # You should have received a copy of the GNU General Public License
REM # along with this program.  If not, see <https://www.gnu.org/licenses/>.

@echo off
REM Build AutoML executable using PyInstaller

setlocal

REM Determine important paths
set "BIN_DIR=%~dp0"
set "REPO_ROOT=%~dp0.."

REM Run from repository root so relative paths resolve correctly
cd /d "%REPO_ROOT%"

REM Warn if running a pre-release Python build which may cause PyInstaller errors
for /f "delims=" %%V in ('python -c "import sys;print(sys.version)"') do set "PYVER=%%V"
echo %PYVER% | findstr /I "alpha beta candidate rc" >nul
if not errorlevel 1 (
    echo Warning: pre-release Python builds can fail with PyInstaller. Use a stable release.
)

REM Verify required Python packages are installed using pip show
python -m pip show pillow >NUL 2>&1 || (
    echo Missing required package 'pillow'. Install with: pip install pillow
    exit /b 1
)

for %%P in (openpyxl networkx matplotlib reportlab adjustText) do (
    python -m pip show %%P >NUL 2>&1 || (
        echo Missing required package '%%P'. Install with: pip install %%P
        exit /b 1
    )
)

REM Generate application icon
python tools\icon_builder.py --output "%BIN_DIR%AutoML.ico" >NUL

REM Use PyInstaller to create the executable
if exist AutoML.spec del AutoML.spec
pyinstaller --noconfirm --onefile --windowed --name AutoML ^
    --exclude-module scipy ^
    --hidden-import=PIL.ImageTk ^
    --hidden-import=tkinter ^
    --hidden-import=tkinter.filedialog ^
    --hidden-import=tkinter.simpledialog ^
    --hidden-import=tkinter.scrolledtext ^
    --hidden-import=tkinter.ttk ^
    --collect-all tools ^
    --add-data "config/styles;config/styles" ^
    --add-data "mainappsrc\core\automl_core.py;mainappsrc\core" ^
    --icon "%BIN_DIR%AutoML.ico" AutoML.py
if errorlevel 1 (
    echo Failed to build executable.
    exit /b %errorlevel%
)

if not exist "%BIN_DIR%" mkdir "%BIN_DIR%"
move /Y dist\AutoML.exe "%BIN_DIR%AutoML.exe" >nul
rmdir /S /Q build 2>nul
rmdir /S /Q dist 2>nul
if exist AutoML.spec del AutoML.spec

python tools\create_installer.py --exe "%BIN_DIR%AutoML.exe" --output "%BIN_DIR%AutoML_installer.zip"

echo Executable and installer created in %BIN_DIR%
