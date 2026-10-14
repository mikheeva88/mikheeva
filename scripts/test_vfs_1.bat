@echo off
cd /d "%~dp0.."
python tools\make_vfs.py vfs_data
echo [1/3] Minimal VFS (one file)
call run.bat --vfs vfs_data\minimal.zip --script examples\vfs_minimal.txt
echo [2/3] Several files
call run.bat --vfs vfs_data\several.zip --script examples\vfs_several.txt
echo [3/3] Three or more levels of folders
call run.bat --vfs vfs_data\deep.zip --script examples\vfs_deep.txt
pause
