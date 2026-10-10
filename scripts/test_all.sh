#!/bin/sh
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RUN="$ROOT/run.sh"
VFSDIR="$ROOT/vfs_data"
EX="$ROOT/examples"
python3 "$ROOT/tools/make_vfs.py" "$VFSDIR"

echo "[1/2] All commands and modes on deep.zip (stages 1-3)"
"$RUN" --vfs "$VFSDIR/deep.zip" --script "$EX/all_commands.txt"
echo "[2/2] exit inside a script (window closes)"
"$RUN" --vfs "$VFSDIR/deep.zip" --script "$EX/with_exit.txt"
