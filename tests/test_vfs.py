import os
import tempfile
import unittest
import zipfile

import emulator


def make_zip(folder, entries, name="test.zip"):
    path = os.path.join(folder, name)
    with zipfile.ZipFile(path, "w") as archive:
        for entry, data in entries:
            archive.writestr(entry, data)
    return path


class TestVfs(unittest.TestCase):
    def test_tree(self):
        entries = [("a.txt", "12"), ("d/", ""), ("d/e/f.txt", b"x")]
        with tempfile.TemporaryDirectory() as folder:
            vfs = emulator.load_vfs(make_zip(folder, entries))
            self.assertEqual(os.listdir(folder), ["test.zip"])
        expected = {"a.txt": b"12", "d": {"e": {"f.txt": b"x"}}}
        self.assertEqual(vfs, expected)

    def test_errors(self):
        with tempfile.TemporaryDirectory() as folder:
            fake = os.path.join(folder, "fake.zip")
            with open(fake, "w", encoding="utf-8") as fake_file:
                fake_file.write("not a zip")
            bad = [
                os.path.join(folder, "missing.zip"),
                folder,
                fake,
                make_zip(folder, [("../evil.txt", "x")], "a.zip"),
                make_zip(folder, [("a", "x"), ("a/b", "y")], "b.zip"),
            ]
            for path in bad:
                with self.assertRaises(emulator.VfsError, msg=path):
                    emulator.load_vfs(path)
