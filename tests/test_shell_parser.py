"""Тесты парсера строки ввода."""

import unittest

from emulator.shell_parser import ParseError, parse_line


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

    def test_double_quotes(self):
        """Двойные кавычки объединяют слова в один аргумент."""
        parsed = parse_line('echo "a   b" c')
        self.assertEqual(parsed.args, ["a   b", "c"])

    def test_single_quotes(self):
        """Одинарные кавычки тоже объединяют слова."""
        parsed = parse_line("echo 'a  b'")
        self.assertEqual(parsed.args, ["a  b"])

    def test_unclosed_quote(self):
        """Незакрытая кавычка — ошибка разбора."""
        with self.assertRaises(ParseError):
            parse_line('echo "abc')

    def test_empty_line(self):
        """Пустая строка даёт None."""
        self.assertIsNone(parse_line(""))

    def test_spaces_only(self):
        """Строка из одних пробелов даёт None."""
        self.assertIsNone(parse_line("   \t "))


if __name__ == "__main__":
    unittest.main()
