@echo off
for %%I in ("%~dp0..") do set "ROOT=%%~fI"
set "RUN=%ROOT%\run.bat"
set "VFSDIR=%ROOT%\vfs_data"
set "EX=%ROOT%\examples"
python "%ROOT%\tools\make_vfs.py" "%VFSDIR%"

echo [1/4] Script with erroneous lines (errors are shown, execution continues)
call "%RUN%" --vfs "%VFSDIR%\minimal.zip" --script "%EX%\with_errors.txt"
echo [2/4] Script file does not exist (error message, interactive mode works)
call "%RUN%" --vfs "%VFSDIR%\minimal.zip" --script "%EX%\no_such_file.txt"
echo [3/4] Script with exit (window closes after exit)
call "%RUN%" --vfs "%VFSDIR%\minimal.zip" --script "%EX%\with_exit.txt"
echo [4/4] Unknown parameter (argparse error, window does not open)
call "%RUN%" --vfs "%VFSDIR%\minimal.zip" --script "%EX%\basic.txt" --unknown 1
pause
