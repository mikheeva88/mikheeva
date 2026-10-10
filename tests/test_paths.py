"""Тесты нормализации путей и сеанса."""

import unittest

from emulator.errors import CommandError
from emulator.paths import normalize
from emulator.session import Session


class TestNormalize(unittest.TestCase):
    """Проверка функции normalize."""

    def test_absolute(self):
        """Абсолютный путь не зависит от текущего каталога."""
        self.assertEqual(normalize("/x/y", "/a/b"), "/a/b")

    def test_relative(self):
        """Относительный путь добавляется к текущему каталогу."""
        self.assertEqual(normalize("/x", "a/b"), "/x/a/b")

    def test_dots(self):
        """«.» и «..» обрабатываются."""
        self.assertEqual(normalize("/x/y", "./../z/./w/.."), "/x/z")

    def test_above_root(self):
        """Подъём выше корня остаётся в корне."""
        self.assertEqual(normalize("/", "../../a"), "/a")

    def test_empty_and_root(self):
        """Пустой путь — текущий каталог, «/» — корень."""
        self.assertEqual(normalize("/x", ""), "/x")
        self.assertEqual(normalize("/x", "/"), "/")


class TestSession(unittest.TestCase):
    """Проверка методов Session."""

    def test_require_vfs(self):
        """Без VFS require_vfs вызывает CommandError."""
        with self.assertRaises(CommandError):
            Session().require_vfs()

    def test_lookup_without_vfs(self):
        """Без VFS lookup тоже вызывает CommandError."""
        with self.assertRaises(CommandError):
            Session().lookup("/a")


if __name__ == "__main__":
    unittest.main()
