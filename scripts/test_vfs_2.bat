@echo off
cd /d "%~dp0.."
python tools\make_vfs.py vfs_data
echo [1/6] All commands on the minimal VFS
call run.bat --vfs vfs_data\minimal.zip --script examples\main_commands.txt
echo [2/6] All commands on the VFS with several files
call run.bat --vfs vfs_data\several.zip --script examples\main_commands.txt
echo [3/6] All commands on the deep VFS
call run.bat --vfs vfs_data\deep.zip --script examples\main_commands.txt
echo [4/6] Archive does not exist (error, emulator keeps working)
call run.bat --vfs vfs_data\no_such.zip --script examples\vfs_minimal.txt
echo [5/6] File is not a ZIP archive
call run.bat --vfs vfs_data\broken.zip --script examples\vfs_minimal.txt
echo [6/6] Archive with unsafe path (../evil.txt)
call run.bat --vfs vfs_data\traversal.zip --script examples\vfs_minimal.txt
pause
