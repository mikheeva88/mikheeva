"""Тесты команд эмулятора."""

import unittest

from emulator.commands import execute


class TestStubs(unittest.TestCase):
    """Проверка команд-заглушек ls и cd."""

    def test_ls_without_args(self):
        """ls без аргументов выводит имя и «(нет)»."""
        result = execute("ls")
        self.assertIn("ls", result.output)
        self.assertIn("(нет)", result.output)
        self.assertFalse(result.is_error)
        self.assertFalse(result.should_exit)

    def test_ls_with_args(self):
        """ls выводит все переданные аргументы."""
        result = execute("ls -l /tmp")
        self.assertIn("-l /tmp", result.output)

    def test_cd_with_args(self):
        """cd выводит своё имя и аргументы."""
        result = execute("cd docs")
        self.assertIn("cd", result.output)
        self.assertIn("docs", result.output)
        self.assertFalse(result.is_error)


class TestExit(unittest.TestCase):
    """Проверка команды exit."""

    def test_exit(self):
        """exit просит завершить эмулятор."""
        result = execute("exit")
        self.assertTrue(result.should_exit)
        self.assertFalse(result.is_error)

    def test_exit_with_args(self):
        """exit с аргументами — ошибка, завершения нет."""
        result = execute("exit now")
        self.assertTrue(result.is_error)
        self.assertFalse(result.should_exit)


class TestErrors(unittest.TestCase):
    """Проверка обработки ошибочного ввода."""

    def test_unknown_command(self):
        """Неизвестная команда даёт сообщение об ошибке."""
        result = execute("foo bar")
        self.assertTrue(result.is_error)
        self.assertIn("foo", result.output)

    def test_empty_input(self):
        """Пустой ввод ничего не выводит и не считается ошибкой."""
        result = execute("   ")
        self.assertEqual(result.output, "")
        self.assertFalse(result.is_error)
        self.assertFalse(result.should_exit)


if __name__ == "__main__":
    unittest.main()
