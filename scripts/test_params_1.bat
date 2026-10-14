@echo off
cd /d "%~dp0.."
python tools\make_vfs.py vfs_data
echo [1/4] No parameters
call run.bat
echo [2/4] Only --vfs
call run.bat --vfs vfs_data\minimal.zip
echo [3/4] Only --script
call run.bat --script examples\basic.txt
echo [4/4] Both parameters
call run.bat --vfs vfs_data\minimal.zip --script examples\basic.txt
pause
