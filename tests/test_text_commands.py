"""Тесты команд echo и tac."""

import base64
import unittest

from emulator.commands import execute
from emulator.text_commands import reverse_lines
from zip_helper import SessionTestCase

BINARY = bytes([0x89, 0x50, 0x0A, 0xFF, 0x00, 0x0A, 0x01])
ENTRIES = [
    ("two.txt", b"first\nsecond\n"),
    ("no_newline.txt", b"a\nb"),
    ("blank.txt", b"x\n\ny\n"),
    ("one.txt", "один\n".encode("utf-8")),
    ("empty.txt", b""),
    ("bin.dat", BINARY),
    ("dir/", b""),
]


class TestEcho(unittest.TestCase):
    """Проверка команды echo."""

    def test_words(self):
        """Аргументы выводятся через один пробел."""
        self.assertEqual(execute("echo a   b  c").output, "a b c")

    def test_quotes(self):
        """В кавычках пробелы сохраняются."""
        self.assertEqual(execute('echo "a   b"').output, "a   b")

    def test_no_args(self):
        """Без аргументов вывод пустой."""
        result = execute("echo")
        self.assertEqual(result.output, "")
        self.assertFalse(result.is_error)

    def test_escapes_off_by_default(self):
        """Без -e последовательности не обрабатываются."""
        self.assertEqual(execute('echo "a\\nb"').output, "a\\nb")

    def test_escapes(self):
        """С -e обрабатываются \\n, \\t и \\\\."""
        result = execute('echo -e "a\\nb\\tc\\\\d"')
        self.assertEqual(result.output, "a\nb\tc\\d")

    def test_unknown_escape(self):
        """Неизвестная последовательность остаётся как есть."""
        self.assertEqual(execute('echo -e "a\\qb"').output, "a\\qb")

    def test_works_without_vfs(self):
        """echo не требует VFS."""
        self.assertFalse(execute("echo hi").is_error)


class TestReverseLines(unittest.TestCase):
    """Проверка функции reverse_lines."""

    def test_with_trailing_newline(self):
        """Строки идут в обратном порядке."""
        self.assertEqual(reverse_lines(b"a\nb\nc\n"), b"c\nb\na")

    def test_without_trailing_newline(self):
        """Последняя строка без перевода строки тоже переворачивается."""
        self.assertEqual(reverse_lines(b"a\nb"), b"b\na")

    def test_blank_lines(self):
        """Пустые строки сохраняются."""
        self.assertEqual(reverse_lines(b"x\n\ny\n"), b"y\n\nx")

    def test_empty(self):
        """Пустые данные дают пустой результат."""
        self.assertEqual(reverse_lines(b""), b"")


class TestTac(SessionTestCase):
    """Проверка команды tac."""

    ENTRIES = ENTRIES

    def test_single_file(self):
        """Строки файла выводятся с конца."""
        self.assertEqual(self.run_line("tac two.txt").output,
                         "second\nfirst")

    def test_no_trailing_newline(self):
        """Файл без завершающего перевода строки."""
        self.assertEqual(self.run_line("tac no_newline.txt").output, "b\na")

    def test_blank_lines(self):
        """Пустые строки сохраняются."""
        self.assertEqual(self.run_line("tac blank.txt").output, "y\n\nx")

    def test_several_files(self):
        """Каждый файл переворачивается отдельно, в порядке аргументов."""
        result = self.run_line("tac two.txt one.txt")
        self.assertEqual(result.output, "second\nfirst\nодин")

    def test_empty_file(self):
        """Пустой файл ничего не выводит."""
        result = self.run_line("tac empty.txt")
        self.assertEqual(result.output, "")
        self.assertFalse(result.is_error)

    def test_binary_base64(self):
        """Двоичный файл: строки в обратном порядке, вывод в base64."""
        header, encoded = self.run_line("tac bin.dat").output.split("\n")
        self.assertIn("base64", header)
        expected = bytes([0x01, 0x0A, 0xFF, 0x00, 0x0A, 0x89, 0x50])
        self.assertEqual(base64.b64decode(encoded), expected)

    def test_relative_path(self):
        """Путь считается от текущего каталога."""
        self.run_line("cd dir")
        self.assertEqual(self.run_line("tac ../one.txt").output, "один")

    def test_no_args(self):
        """Без аргументов — ошибка использования."""
        result = self.run_line("tac")
        self.assertTrue(result.is_error)
        self.assertIn("использование", result.output)

    def test_directory(self):
        """Каталог — ошибка."""
        result = self.run_line("tac dir")
        self.assertEqual(result.output, "tac: dir: это каталог")

    def test_missing_file_blocks_output(self):
        """Если один из файлов не найден, выводится только ошибка."""
        result = self.run_line("tac two.txt nope.txt")
        self.assertTrue(result.is_error)
        self.assertNotIn("second", result.output)

    def test_without_vfs(self):
        """Без VFS tac сообщает об ошибке."""
        self.session.vfs = None
        self.assertTrue(self.run_line("tac two.txt").is_error)


if __name__ == "__main__":
    unittest.main()
