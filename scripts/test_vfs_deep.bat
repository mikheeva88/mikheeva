@echo off
for %%I in ("%~dp0..") do set "ROOT=%%~fI"
set "RUN=%ROOT%\run.bat"
set "VFSDIR=%ROOT%\vfs_data"
set "EX=%ROOT%\examples"
python "%ROOT%\tools\make_vfs.py" "%VFSDIR%"

echo VFS variant: deep.zip
call "%RUN%" --vfs "%VFSDIR%\deep.zip" --script "%EX%\vfs_deep.txt"
pause
