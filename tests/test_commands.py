import unittest

import emulator

OK = [
    ('echo a   "b   c"', "a b   c"),
    ("ls -l b.txt", "- root root      1 b.txt"),
    ("tac docs/a.txt b.txt", "two\none\nb"),
    ("chown bob:dev b.txt", ""),
    ("ls -l b.txt", "- bob dev      1 b.txt"),
    ("rmdir empty", ""),
    ("ls", "b.txt\nbin.dat\ndocs/"),
    ("cd docs/deep", ""),
    ("ls ../..", "b.txt\nbin.dat\ndocs/"),
]
ERRORS = [
    "foo", 'echo "x', "exit now", "ls nope", "ls -z", "ls docs docs",
    "cd nope", "cd b.txt", "cd docs docs", "tac", "tac nope", "tac docs",
    "rmdir", "rmdir nope", "rmdir b.txt", "rmdir docs", "rmdir /",
    "chown", "chown bob", "chown :g b.txt", "chown bob nope",
]


class TestCommands(unittest.TestCase):
    def setUp(self):
        docs = {"a.txt": b"one\ntwo\n", "deep": {"x.txt": b"x"}}
        binary = b"\x89\n\xff\x00"
        vfs = {"b.txt": b"b", "bin.dat": binary, "docs": docs, "empty": {}}
        self.shell = emulator.Shell(vfs)

    def test_sequence(self):
        for line, output in OK:
            self.assertEqual(self.shell.run(line).output, output, line)
        self.assertEqual(self.shell.cwd, "/docs/deep")

    def test_errors(self):
        for line in ERRORS:
            self.assertTrue(self.shell.run(line).is_error, line)

    def test_binary_and_exit(self):
        output = self.shell.run("tac bin.dat").output
        self.assertEqual(output, "(двоичный файл, base64)\n/wAKiQ==")
        self.assertTrue(self.shell.run("exit").should_exit)

    def test_current_dir_and_missing_path(self):
        self.shell.run("cd empty")
        self.assertIn("текущий", self.shell.run("rmdir .").output)
        self.shell.run("chown bob b.txt nope")
        self.assertIn("root", self.shell.run("ls -l /b.txt").output)

