@echo off
for %%I in ("%~dp0..") do set "ROOT=%%~fI"
set "RUN=%ROOT%\run.bat"
set "VFSDIR=%ROOT%\vfs_data"
set "EX=%ROOT%\examples"
python "%ROOT%\tools\make_vfs.py" "%VFSDIR%"

echo [1/2] All commands and modes on deep.zip (stages 1-3)
call "%RUN%" --vfs "%VFSDIR%\deep.zip" --script "%EX%\all_commands.txt"
echo [2/2] exit inside a script (window closes)
call "%RUN%" --vfs "%VFSDIR%\deep.zip" --script "%EX%\with_exit.txt"
pause
