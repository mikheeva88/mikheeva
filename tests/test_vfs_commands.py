"""Тесты служебных команд VFS: vfs-info, vfs-tree, vfs-show."""

import base64
import unittest

from emulator.commands import execute
from zip_helper import SessionTestCase

BINARY = bytes([0x89, 0x50, 0xFF, 0x00, 0x01])
ENTRIES = [
    ("readme.txt", "Привет\nмир\n".encode("utf-8")),
    ("empty.txt", b""),
    ("bin.dat", BINARY),
    ("docs/guide.txt", b"guide"),
    ("docs/deep/x.txt", b"x"),
    ("void/", b""),
]
TREE = "\n".join([
    "/",
    "|-- docs/",
    "|   |-- deep/",
    "|   |   `-- x.txt (1 B)",
    "|   `-- guide.txt (5 B)",
    "|-- void/",
    "|-- bin.dat (5 B)",
    "|-- empty.txt (0 B)",
    "`-- readme.txt (20 B)",
])


class VfsCommandsTestCase(SessionTestCase):
    """Базовый класс: сеанс с тестовой VFS."""

    ENTRIES = ENTRIES


class TestVfsInfo(VfsCommandsTestCase):
    """Проверка vfs-info."""

    def test_info(self):
        """Выводятся источник и статистика."""
        result = self.run_line("vfs-info")
        self.assertFalse(result.is_error)
        self.assertIn(self.vfs.source, result.output)
        self.assertIn("Каталогов (без корня): 3", result.output)
        self.assertIn("Файлов: 5", result.output)
        self.assertIn("Общий размер: 31 B", result.output)

    def test_extra_args(self):
        """Лишние аргументы — ошибка."""
        self.assertTrue(self.run_line("vfs-info now").is_error)


class TestVfsTree(VfsCommandsTestCase):
    """Проверка vfs-tree."""

    def test_tree(self):
        """Дерево: сначала каталоги, потом файлы, с отступами."""
        self.assertEqual(self.run_line("vfs-tree").output, TREE)

    def test_extra_args(self):
        """Лишние аргументы — ошибка."""
        self.assertTrue(self.run_line("vfs-tree now").is_error)


class TestVfsShow(VfsCommandsTestCase):
    """Проверка vfs-show."""

    def test_text(self):
        """Текст выводится как есть."""
        result = self.run_line("vfs-show readme.txt")
        self.assertEqual(result.output, "Привет\nмир")
        self.assertFalse(result.is_error)

    def test_absolute_path(self):
        """Путь можно писать с корня."""
        result = self.run_line("vfs-show /docs/guide.txt")
        self.assertEqual(result.output, "guide")

    def test_binary_base64(self):
        """Двоичный файл выводится в base64."""
        result = self.run_line("vfs-show bin.dat")
        header, encoded = result.output.split("\n")
        self.assertIn("base64", header)
        self.assertEqual(base64.b64decode(encoded), BINARY)

    def test_empty_file(self):
        """Пустой файл помечается особо."""
        self.assertEqual(self.run_line("vfs-show empty.txt").output,
                         "(файл пуст)")

    def test_directory(self):
        """Каталог — ошибка."""
        self.assertTrue(self.run_line("vfs-show docs").is_error)

    def test_missing(self):
        """Несуществующий путь — ошибка."""
        result = self.run_line("vfs-show nope.txt")
        self.assertTrue(result.is_error)
        self.assertIn("nope.txt", result.output)

    def test_relative_to_cwd(self):
        """Путь считается от текущего каталога."""
        self.run_line("cd docs")
        self.assertEqual(self.run_line("vfs-show guide.txt").output, "guide")
        self.assertEqual(self.run_line("vfs-show ../empty.txt").output,
                         "(файл пуст)")

    def test_wrong_arg_count(self):
        """Без аргументов и с двумя — ошибка использования."""
        self.assertTrue(self.run_line("vfs-show").is_error)
        self.assertTrue(self.run_line("vfs-show a b").is_error)


class TestWithoutVfs(unittest.TestCase):
    """Все команды VFS без загруженной VFS — ошибка."""

    def test_errors(self):
        """Сообщение подсказывает про параметр --vfs."""
        for line in ["vfs-info", "vfs-tree", "vfs-show a.txt"]:
            result = execute(line)
            self.assertTrue(result.is_error, line)
            self.assertIn("--vfs", result.output)


if __name__ == "__main__":
    unittest.main()
