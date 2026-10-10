#!/bin/sh
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RUN="$ROOT/run.sh"
VFSDIR="$ROOT/vfs_data"
EX="$ROOT/examples"
python3 "$ROOT/tools/make_vfs.py" "$VFSDIR"

echo "VFS variant: several.zip"
"$RUN" --vfs "$VFSDIR/several.zip" --script "$EX/vfs_several.txt"
