#!/bin/sh
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RUN="$ROOT/run.sh"
VFS="$ROOT/vfs_data"

echo "[1/4] Syntax --vfs=PATH --script=PATH"
"$RUN" --vfs="$VFS" --script="$ROOT/examples/basic.txt"
echo "[2/4] Reversed order of parameters"
"$RUN" --script "$ROOT/examples/basic.txt" --vfs "$VFS"
echo "[3/4] Parameter without value (argparse error, window does not open)"
"$RUN" --script "$ROOT/examples/basic.txt" --vfs
echo "[4/4] Help for --vfs and --script (printed to console)"
"$RUN" --help
