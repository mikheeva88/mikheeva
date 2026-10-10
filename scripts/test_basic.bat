@echo off
for %%I in ("%~dp0..") do set "ROOT=%%~fI"
set "RUN=%ROOT%\run.bat"
set "VFSDIR=%ROOT%\vfs_data"
set "EX=%ROOT%\examples"
python "%ROOT%\tools\make_vfs.py" "%VFSDIR%"

echo [1/4] No parameters
call "%RUN%"
echo [2/4] Only --vfs
call "%RUN%" --vfs "%VFSDIR%\minimal.zip"
echo [3/4] Only --script
call "%RUN%" --script "%EX%\basic.txt"
echo [4/4] Both parameters
call "%RUN%" --vfs "%VFSDIR%\minimal.zip" --script "%EX%\basic.txt"
pause
