@echo off
rem aipollo CLI shim — runs the project's main.py
setlocal
set SCRIPT_DIR=%~dp0
pushd "%SCRIPT_DIR%"
rem Prefer Python on PATH, then fall back to the Windows Python launcher.
where python >nul 2>&1
if not errorlevel 1 (
	python "%SCRIPT_DIR%main.py" %*
) else (
	py -3 "%SCRIPT_DIR%main.py" %*
)
set EXIT_CODE=%ERRORLEVEL%
popd
endlocal
exit /b %EXIT_CODE%
