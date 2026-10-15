import os
import subprocess
import sys
import tempfile
import unittest

import emulator

ROOT = os.path.join(os.path.dirname(__file__), os.pardir)
TOOL = os.path.join(ROOT, "tools", "make_vfs.py")
CASES = [
    ("basic.txt", None, 0),
    ("with_errors.txt", None, 3),
    ("vfs_minimal.txt", "minimal.zip", 1),
    ("vfs_several.txt", "several.zip", 3),
    ("vfs_deep.txt", "deep.zip", 2),
    ("main_commands.txt", "deep.zip", 11),
    ("stage5_commands.txt", "deep.zip", 12),
]


class TestScript(unittest.TestCase):
    def test_examples(self):
        with tempfile.TemporaryDirectory() as folder:
            command = [sys.executable, TOOL, folder]
            subprocess.run(command, check=True, capture_output=True)
            for script, archive, count in CASES:
                vfs = {}
                if archive:
                    vfs = emulator.load_vfs(os.path.join(folder, archive))
                lines = emulator.read_script(f"{ROOT}/examples/{script}")
                shell = emulator.Shell(vfs)
                errors = [x for x in lines if shell.run(x).is_error]
                self.assertEqual(len(errors), count, script)

    def test_read_script(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "script.txt")
            with open(path, "w", encoding="utf-8-sig") as script_file:
                script_file.write("# c\n\n  echo a  \nls\n")
            self.assertEqual(emulator.read_script(path), ["echo a", "ls"])

    def test_options(self):
        args = emulator.parse_args(["--script=b.txt", "--vfs", "a.zip"])
        self.assertEqual((args.vfs, args.script), ("a.zip", "b.txt"))
