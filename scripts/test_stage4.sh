#!/bin/sh
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RUN="$ROOT/run.sh"
VFSDIR="$ROOT/vfs_data"
EX="$ROOT/examples"
python3 "$ROOT/tools/make_vfs.py" "$VFSDIR"

echo "[1/3] Stage 4 commands on deep.zip: ls, cd, echo, tac (modes and errors)"
"$RUN" --vfs "$VFSDIR/deep.zip" --script "$EX/main_commands.txt"
echo "[2/3] Same script on several.zip (other files, missing paths give errors)"
"$RUN" --vfs "$VFSDIR/several.zip" --script "$EX/main_commands.txt"
echo "[3/3] Same script without --vfs (ls, cd and tac report that VFS is not loaded)"
"$RUN" --script "$EX/main_commands.txt"
