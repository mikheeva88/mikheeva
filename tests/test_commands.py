"""Тесты выполнения команд: exit, ошибки ввода, диспетчер."""

import unittest

from emulator.commands import execute
from emulator.session import Session


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
        self.assertEqual(result.output, "exit: слишком много аргументов")


class TestErrors(unittest.TestCase):
    """Проверка обработки ошибочного ввода."""

    def test_unknown_command(self):
        """Неизвестная команда даёт сообщение об ошибке."""
        result = execute("foo bar")
        self.assertTrue(result.is_error)
        self.assertEqual(result.output, "foo: команда не найдена")

    def test_empty_input(self):
        """Пустой ввод ничего не выводит и не считается ошибкой."""
        result = execute("   ")
        self.assertEqual(result.output, "")
        self.assertFalse(result.is_error)
        self.assertFalse(result.should_exit)

    def test_syntax_error(self):
        """Незакрытая кавычка даёт синтаксическую ошибку."""
        result = execute('echo "abc')
        self.assertTrue(result.is_error)
        self.assertIn("синтаксическая ошибка", result.output)


class TestSession(unittest.TestCase):
    """Проверка работы с сеансом."""

    def test_default_session(self):
        """Без сеанса команды работают, но VFS нет."""
        self.assertEqual(execute("echo hi").output, "hi")
        self.assertTrue(execute("ls").is_error)

    def test_session_is_kept(self):
        """Один и тот же сеанс сохраняется между командами."""
        session = Session()
        execute("echo hi", session)
        self.assertEqual(session.cwd, "/")


if __name__ == "__main__":
    unittest.main()
