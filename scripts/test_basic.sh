#!/bin/sh
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RUN="$ROOT/run.sh"
VFS="$ROOT/vfs_data"

echo "[1/4] No parameters"
"$RUN"
echo "[2/4] Only --vfs"
"$RUN" --vfs "$VFS"
echo "[3/4] Only --script"
"$RUN" --script "$ROOT/examples/basic.txt"
echo "[4/4] Both parameters"
"$RUN" --vfs "$VFS" --script "$ROOT/examples/basic.txt"
