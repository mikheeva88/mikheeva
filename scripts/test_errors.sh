#!/bin/sh
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RUN="$ROOT/run.sh"
VFS="$ROOT/vfs_data"

echo "[1/4] Script with erroneous lines (errors are shown, execution continues)"
"$RUN" --vfs "$VFS" --script "$ROOT/examples/with_errors.txt"
echo "[2/4] Script file does not exist (error message, interactive mode works)"
"$RUN" --vfs "$VFS" --script "$ROOT/examples/no_such_file.txt"
echo "[3/4] Script with exit (window closes after exit)"
"$RUN" --vfs "$VFS" --script "$ROOT/examples/with_exit.txt"
echo "[4/4] Unknown parameter (argparse error, window does not open)"
"$RUN" --vfs "$VFS" --script "$ROOT/examples/basic.txt" --unknown 1
