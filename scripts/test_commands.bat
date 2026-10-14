@echo off
cd /d "%~dp0.."
python tools\make_vfs.py vfs_data
echo [1/3] Stage 4: ls, cd, echo, tac
call run.bat --vfs vfs_data\deep.zip --script examples\main_commands.txt
echo [2/3] Stage 5: rmdir, chown, ls -l
call run.bat --vfs vfs_data\deep.zip --script examples\stage5_commands.txt
echo [3/3] Stage 5 again: the archive is unchanged, everything is back
call run.bat --vfs vfs_data\deep.zip --script examples\stage5_commands.txt
pause
