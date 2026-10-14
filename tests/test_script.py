import os
import subprocess
import sys
import tempfile
import unittest

import emulator

ROOT = os.path.join(os.path.dirname(__file__), os.pardir)
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
    @classmethod
    def setUpClass(cls):
        cls.folder = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.folder.cleanup)
        tool = os.path.join(ROOT, "tools", "make_vfs.py")
        subprocess.run([sys.executable, tool, cls.folder.name],
                       check=True, capture_output=True)

    def test_examples(self):
        for script, archive, count in CASES:
            vfs = {}
            if archive:
                path = os.path.join(self.folder.name, archive)
                vfs = emulator.load_vfs(path)
            lines = emulator.read_script(f"{ROOT}/examples/{script}")
            shell = emulator.Shell(vfs)
            errors = [line for line in lines if shell.run(line).is_error]
            self.assertEqual(len(errors), count, script)

    def test_read_script(self):
        path = os.path.join(self.folder.name, "script.txt")
        with open(path, "w", encoding="utf-8-sig") as script_file:
            script_file.write("# c\n\n  echo a  \nls\n")
        self.assertEqual(emulator.read_script(path), ["echo a", "ls"])

    def test_options(self):
        args = emulator.parse_args(["--script=b.txt", "--vfs", "a.zip"])
        self.assertEqual((args.vfs, args.script), ("a.zip", "b.txt"))

