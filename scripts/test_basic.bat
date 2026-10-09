@echo off
for %%I in ("%~dp0..") do set "ROOT=%%~fI"
set "RUN=%ROOT%\run.bat"
set "VFS=%ROOT%\vfs_data"

echo [1/4] No parameters
call "%RUN%"
echo [2/4] Only --vfs
call "%RUN%" --vfs "%VFS%"
echo [3/4] Only --script
call "%RUN%" --script "%ROOT%\examples\basic.txt"
echo [4/4] Both parameters
call "%RUN%" --vfs "%VFS%" --script "%ROOT%\examples\basic.txt"
pause
