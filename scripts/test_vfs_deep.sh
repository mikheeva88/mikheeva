#!/bin/sh
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RUN="$ROOT/run.sh"
VFSDIR="$ROOT/vfs_data"
EX="$ROOT/examples"
python3 "$ROOT/tools/make_vfs.py" "$VFSDIR"

echo "VFS variant: deep.zip"
"$RUN" --vfs "$VFSDIR/deep.zip" --script "$EX/vfs_deep.txt"
