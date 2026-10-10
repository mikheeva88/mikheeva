#!/bin/sh
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RUN="$ROOT/run.sh"
VFSDIR="$ROOT/vfs_data"
EX="$ROOT/examples"
python3 "$ROOT/tools/make_vfs.py" "$VFSDIR"

echo "[1/4] Script with erroneous lines (errors are shown, execution continues)"
"$RUN" --vfs "$VFSDIR/minimal.zip" --script "$EX/with_errors.txt"
echo "[2/4] Script file does not exist (error message, interactive mode works)"
"$RUN" --vfs "$VFSDIR/minimal.zip" --script "$EX/no_such_file.txt"
echo "[3/4] Script with exit (window closes after exit)"
"$RUN" --vfs "$VFSDIR/minimal.zip" --script "$EX/with_exit.txt"
echo "[4/4] Unknown parameter (argparse error, window does not open)"
"$RUN" --vfs "$VFSDIR/minimal.zip" --script "$EX/basic.txt" --unknown 1
