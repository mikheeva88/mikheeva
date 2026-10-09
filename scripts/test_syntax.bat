@echo off
for %%I in ("%~dp0..") do set "ROOT=%%~fI"
set "RUN=%ROOT%\run.bat"
set "VFS=%ROOT%\vfs_data"

echo [1/4] Syntax --vfs=PATH --script=PATH
call "%RUN%" "--vfs=%VFS%" "--script=%ROOT%\examples\basic.txt"
echo [2/4] Reversed order of parameters
call "%RUN%" --script "%ROOT%\examples\basic.txt" --vfs "%VFS%"
echo [3/4] Parameter without value (argparse error, window does not open)
call "%RUN%" --script "%ROOT%\examples\basic.txt" --vfs
echo [4/4] Help for --vfs and --script (printed to console)
call "%RUN%" --help
pause
