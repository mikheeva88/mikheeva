"""Тесты параметров командной строки."""

import contextlib
import io
import unittest

from emulator.config import Config, format_debug, parse_args


def parse_quietly(argv):
    """Разобрать аргументы, скрыв сообщения argparse об ошибках."""
    with contextlib.redirect_stderr(io.StringIO()):
        return parse_args(argv)


class TestParseArgs(unittest.TestCase):
    """Проверка разбора параметров --vfs и --script."""

    def test_no_args(self):
        """Без параметров все значения не заданы."""
        self.assertEqual(parse_args([]), Config(None, None))

    def test_both_args(self):
        """Оба параметра с отдельными значениями."""
        config = parse_args(["--vfs", "a/vfs", "--script", "b.txt"])
        self.assertEqual(config.vfs_path, "a/vfs")
        self.assertEqual(config.script_path, "b.txt")

    def test_only_vfs(self):
        """Задан только --vfs."""
        config = parse_args(["--vfs", "a/vfs"])
        self.assertEqual(config.vfs_path, "a/vfs")
        self.assertIsNone(config.script_path)

    def test_only_script(self):
        """Задан только --script."""
        config = parse_args(["--script", "b.txt"])
        self.assertIsNone(config.vfs_path)
        self.assertEqual(config.script_path, "b.txt")

    def test_equals_syntax(self):
        """Синтаксис --параметр=значение."""
        config = parse_args(["--vfs=x", "--script=y"])
        self.assertEqual(config, Config("x", "y"))

    def test_reversed_order(self):
        """Порядок параметров не важен."""
        config = parse_args(["--script", "y", "--vfs", "x"])
        self.assertEqual(config, Config("x", "y"))

    def test_unknown_option(self):
        """Неизвестный параметр завершает разбор ошибкой."""
        with self.assertRaises(SystemExit):
            parse_quietly(["--unknown", "1"])

    def test_missing_value(self):
        """Параметр без значения — ошибка."""
        with self.assertRaises(SystemExit):
            parse_quietly(["--vfs"])

    def test_abbreviation_not_allowed(self):
        """Сокращённые имена параметров не принимаются."""
        with self.assertRaises(SystemExit):
            parse_quietly(["--vf", "x"])


class TestFormatDebug(unittest.TestCase):
    """Проверка отладочного вывода параметров."""

    def test_values_are_shown(self):
        """Заданные значения попадают в вывод."""
        text = format_debug(Config("a/vfs", "b.txt"))
        self.assertIn("--vfs    = a/vfs", text)
        self.assertIn("--script = b.txt", text)

    def test_not_set(self):
        """Не заданные параметры помечаются «(не задан)»."""
        text = format_debug(Config())
        self.assertEqual(text.count("(не задан)"), 2)


if __name__ == "__main__":
    unittest.main()
