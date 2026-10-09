"""Тесты парсера строки ввода."""

import unittest

from emulator.shell_parser import parse_line


class TestParseLine(unittest.TestCase):
    """Проверка функции parse_line."""

    def test_command_without_args(self):
        """Одно слово — это команда без аргументов."""
        parsed = parse_line("ls")
        self.assertEqual(parsed.command, "ls")
        self.assertEqual(parsed.args, [])

    def test_command_with_args(self):
        """Первое слово — команда, остальные — аргументы."""
        parsed = parse_line("ls -l /home user")
        self.assertEqual(parsed.command, "ls")
        self.assertEqual(parsed.args, ["-l", "/home", "user"])

    def test_extra_spaces_and_tabs(self):
        """Лишние пробелы и табуляции не создают пустых аргументов."""
        parsed = parse_line("  cd \t  a    b  ")
        self.assertEqual(parsed.command, "cd")
        self.assertEqual(parsed.args, ["a", "b"])

    def test_empty_line(self):
        """Пустая строка даёт None."""
        self.assertIsNone(parse_line(""))

    def test_spaces_only(self):
        """Строка из одних пробелов даёт None."""
        self.assertIsNone(parse_line("   \t "))


if __name__ == "__main__":
    unittest.main()
