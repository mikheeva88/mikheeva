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
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.folder = folder.name

    def test_tree(self):
        entries = [("a.txt", "12"), ("d/", ""), ("d/e/f.txt", b"x"), ("v/", "")]
        vfs = emulator.load_vfs(make_zip(self.folder, entries))
        expected = {"a.txt": b"12", "d": {"e": {"f.txt": b"x"}}, "v": {}}
        self.assertEqual(vfs, expected)
        self.assertEqual(os.listdir(self.folder), ["test.zip"])

    def test_errors(self):
        fake = os.path.join(self.folder, "fake.zip")
        with open(fake, "w", encoding="utf-8") as fake_file:
            fake_file.write("not a zip")
        bad = [
            os.path.join(self.folder, "missing.zip"),
            self.folder,
            fake,
            make_zip(self.folder, [("../evil.txt", "x")], "a.zip"),
            make_zip(self.folder, [("a", "x"), ("a/b", "y")], "b.zip"),
        ]
        for path in bad:
            with self.assertRaises(emulator.VfsError, msg=path):
                emulator.load_vfs(path)

