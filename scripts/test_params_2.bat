@echo off
cd /d "%~dp0.."
python tools\make_vfs.py vfs_data
echo [1/6] Syntax --vfs=PATH --script=PATH
call run.bat "--vfs=vfs_data\minimal.zip" "--script=examples\basic.txt"
echo [2/6] Reversed order of parameters
call run.bat --script examples\basic.txt --vfs vfs_data\minimal.zip
echo [3/6] Script with erroneous lines
call run.bat --vfs vfs_data\minimal.zip --script examples\with_errors.txt
echo [4/6] Script with exit (window closes)
call run.bat --vfs vfs_data\minimal.zip --script examples\with_exit.txt
echo [5/6] Script file does not exist
call run.bat --vfs vfs_data\minimal.zip --script examples\no_such_file.txt
echo [6/6] Unknown parameter, parameter without value, --help (console only)
call run.bat --vfs vfs_data\minimal.zip --script examples\basic.txt --unknown 1
call run.bat --script examples\basic.txt --vfs
call run.bat --help
pause
