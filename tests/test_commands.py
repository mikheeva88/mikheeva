import unittest

import emulator

OK = [
    ('echo a   "b   c"', "a b   c"),
    ("ls -l b.txt", "- root root      1 b.txt"),
    ("tac docs/a.txt b.txt", "two\none\nb"),
    ("tac bin.dat", "(двоичный файл, base64)\n/wAKiQ=="),
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


def make_shell():
    docs = {"a.txt": b"one\ntwo\n", "deep": {"x.txt": b"x"}}
    vfs = {"b.txt": b"b", "bin.dat": b"\x89\n\xff\x00", "empty": {}}
    vfs["docs"] = docs
    return emulator.Shell(vfs)


class TestCommands(unittest.TestCase):
    def test_sequence(self):
        shell = make_shell()
        for line, output in OK:
            self.assertEqual(shell.run(line).output, output, line)
        self.assertEqual(shell.cwd, "/docs/deep")

    def test_errors(self):
        shell = make_shell()
        for line in ERRORS:
            self.assertTrue(shell.run(line).is_error, line)

    def test_protected_state(self):
        shell = make_shell()
        shell.run("cd empty")
        self.assertIn("текущий", shell.run("rmdir .").output)
        shell.run("chown bob b.txt nope")
        self.assertIn("root", shell.run("ls -l /b.txt").output)
        self.assertTrue(shell.run("exit").should_exit)
