@echo off
for %%I in ("%~dp0..") do set "ROOT=%%~fI"
set "RUN=%ROOT%\run.bat"
set "VFSDIR=%ROOT%\vfs_data"
set "EX=%ROOT%\examples"
python "%ROOT%\tools\make_vfs.py" "%VFSDIR%"

echo [1/4] ls, cd, echo, tac on deep.zip (all modes and errors)
call "%RUN%" --vfs "%VFSDIR%\deep.zip" --script "%EX%\main_commands.txt"
echo [2/4] Same script on several.zip (other files, more errors)
call "%RUN%" --vfs "%VFSDIR%\several.zip" --script "%EX%\main_commands.txt"
echo [3/4] Same script without --vfs (empty VFS)
call "%RUN%" --script "%EX%\main_commands.txt"
echo [4/4] exit inside a script (window closes)
call "%RUN%" --vfs "%VFSDIR%\deep.zip" --script "%EX%\with_exit.txt"
pause
