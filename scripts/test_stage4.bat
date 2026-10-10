@echo off
for %%I in ("%~dp0..") do set "ROOT=%%~fI"
set "RUN=%ROOT%\run.bat"
set "VFSDIR=%ROOT%\vfs_data"
set "EX=%ROOT%\examples"
python "%ROOT%\tools\make_vfs.py" "%VFSDIR%"

echo [1/3] Stage 4 commands on deep.zip: ls, cd, echo, tac (modes and errors)
call "%RUN%" --vfs "%VFSDIR%\deep.zip" --script "%EX%\main_commands.txt"
echo [2/3] Same script on several.zip (other files, missing paths give errors)
call "%RUN%" --vfs "%VFSDIR%\several.zip" --script "%EX%\main_commands.txt"
echo [3/3] Same script without --vfs (ls, cd and tac report that VFS is not loaded)
call "%RUN%" --script "%EX%\main_commands.txt"
pause
