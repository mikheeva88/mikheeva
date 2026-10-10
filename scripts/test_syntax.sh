#!/bin/sh
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RUN="$ROOT/run.sh"
VFSDIR="$ROOT/vfs_data"
EX="$ROOT/examples"
python3 "$ROOT/tools/make_vfs.py" "$VFSDIR"

echo "[1/4] Syntax --vfs=PATH --script=PATH"
"$RUN" --vfs="$VFSDIR/minimal.zip" --script="$EX/basic.txt"
echo "[2/4] Reversed order of parameters"
"$RUN" --script "$EX/basic.txt" --vfs "$VFSDIR/minimal.zip"
echo "[3/4] Parameter without value (argparse error, window does not open)"
"$RUN" --script "$EX/basic.txt" --vfs
echo "[4/4] Help for --vfs and --script (printed to console)"
"$RUN" --help
