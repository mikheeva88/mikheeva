@echo off
for %%I in ("%~dp0..") do set "ROOT=%%~fI"
set "RUN=%ROOT%\run.bat"
set "VFSDIR=%ROOT%\vfs_data"
set "EX=%ROOT%\examples"
python "%ROOT%\tools\make_vfs.py" "%VFSDIR%"

echo VFS variant: minimal.zip
call "%RUN%" --vfs "%VFSDIR%\minimal.zip" --script "%EX%\vfs_minimal.txt"
pause
