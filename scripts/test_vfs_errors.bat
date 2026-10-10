@echo off
for %%I in ("%~dp0..") do set "ROOT=%%~fI"
set "RUN=%ROOT%\run.bat"
set "VFSDIR=%ROOT%\vfs_data"
set "EX=%ROOT%\examples"
python "%ROOT%\tools\make_vfs.py" "%VFSDIR%"

echo [1/4] Archive does not exist (error, emulator keeps working without VFS)
call "%RUN%" --vfs "%VFSDIR%\no_such.zip" --script "%EX%\vfs_minimal.txt"
echo [2/4] File is not a ZIP archive
call "%RUN%" --vfs "%VFSDIR%\broken.zip" --script "%EX%\vfs_minimal.txt"
echo [3/4] Archive with unsafe path (../evil.txt)
call "%RUN%" --vfs "%VFSDIR%\traversal.zip" --script "%EX%\vfs_minimal.txt"
echo [4/4] No --vfs at all (every vfs command reports an error)
call "%RUN%" --script "%EX%\vfs_minimal.txt"
pause
