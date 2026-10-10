@echo off
for %%I in ("%~dp0..") do set "ROOT=%%~fI"
set "RUN=%ROOT%\run.bat"
set "VFSDIR=%ROOT%\vfs_data"
set "EX=%ROOT%\examples"
python "%ROOT%\tools\make_vfs.py" "%VFSDIR%"

echo [1/4] Syntax --vfs=PATH --script=PATH
call "%RUN%" "--vfs=%VFSDIR%\minimal.zip" "--script=%EX%\basic.txt"
echo [2/4] Reversed order of parameters
call "%RUN%" --script "%EX%\basic.txt" --vfs "%VFSDIR%\minimal.zip"
echo [3/4] Parameter without value (argparse error, window does not open)
call "%RUN%" --script "%EX%\basic.txt" --vfs
echo [4/4] Help for --vfs and --script (printed to console)
call "%RUN%" --help
pause
