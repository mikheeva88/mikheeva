"""Тесты получения данных ОС и формирования заголовка окна."""

import unittest
from unittest import mock

from emulator import system_info


class TestFormatting(unittest.TestCase):
    """Проверка форматирования заголовка и приглашения."""

    def test_title(self):
        """Заголовок имеет вид «Эмулятор - [user@host]»."""
        title = system_info.format_title("alice", "pc1")
        self.assertEqual(title, "Эмулятор - [alice@pc1]")

    def test_prompt(self):
        """Приглашение имеет вид «user@host:~$»."""
        prompt = system_info.format_prompt("alice", "pc1")
        self.assertEqual(prompt, "alice@pc1:~$")


class TestRealData(unittest.TestCase):
    """Проверка получения данных реальной ОС."""

    def test_username_from_os(self):
        """Имя пользователя берётся из getpass.getuser."""
        with mock.patch("getpass.getuser", return_value="bob"):
            self.assertEqual(system_info.get_username(), "bob")

    def test_username_fallback(self):
        """При ошибке ОС возвращается «unknown»."""
        with mock.patch("getpass.getuser", side_effect=KeyError):
            self.assertEqual(system_info.get_username(), "unknown")

    def test_hostname_from_os(self):
        """Имя компьютера берётся из socket.gethostname."""
        with mock.patch("socket.gethostname", return_value="srv"):
            self.assertEqual(system_info.get_hostname(), "srv")

    def test_hostname_fallback(self):
        """При ошибке ОС возвращается «unknown»."""
        with mock.patch("socket.gethostname", side_effect=OSError):
            self.assertEqual(system_info.get_hostname(), "unknown")


if __name__ == "__main__":
    unittest.main()
