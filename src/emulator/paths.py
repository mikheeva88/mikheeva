"""Работа с путями VFS: приведение к нормальному виду."""

from emulator.vfs import split_path

ROOT_PATH = "/"
PARENT_NAME = ".."


def normalize(cwd: str, path: str) -> str:
    """Преобразовать путь в абсолютный без «.» и «..».

    Args:
        cwd: текущий каталог (абсолютный нормальный путь).
        path: абсолютный или относительный путь.

    Returns:
        Абсолютный путь вида «/a/b». Подъём выше корня остаётся в корне.
    """
    parts = [] if path.startswith(ROOT_PATH) else split_path(cwd)
    for part in split_path(path):
        if part != PARENT_NAME:
            parts.append(part)
        elif parts:
            parts.pop()
    return ROOT_PATH + "/".join(parts)
