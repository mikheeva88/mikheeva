#!/bin/sh
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RUN="$ROOT/run.sh"
VFSDIR="$ROOT/vfs_data"
EX="$ROOT/examples"
python3 "$ROOT/tools/make_vfs.py" "$VFSDIR"

echo "VFS variant: minimal.zip"
"$RUN" --vfs "$VFSDIR/minimal.zip" --script "$EX/vfs_minimal.txt"
