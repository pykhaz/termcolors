import pytest
from random import sample
import sys

from importlib import reload
from termcolors import cli

reload(cli)
ARST = "\033[0m"  # wyłącza wszystkie efekty


def test_integration(monkeypatch, capsys):

    # symulujemy brak argumentów w CLI
    monkeypatch.setattr(sys, "argv", ["termcolors"])

    # for _ in range(10):
    r, g, b = sample(range(0, 256), 3)
    inputs = iter([f"{r};{g};{b}", "fg", "quit"])
    monkeypatch.setattr("builtins.input", lambda: next(inputs))

    cli.main()

    captured = capsys.readouterr()
    print(f"{ARST}")
    # print(f"{captured.out = }")

    assert f"38;2;{r};{g};{b}m" in captured.out


def test_integration_full(monkeypatch, capsys):
    # symulujemy brak argumentów w CLI
    monkeypatch.setattr(sys, "argv", ["termcolors"])

    # losowy kolor RGB
    r, g, b = sample(range(0, 256), 3)

    # kolejność wejścia: kolor -> fg -> quit
    inputs = iter([f"{r};{g};{b}", "fg", "quit"])
    monkeypatch.setattr("builtins.input", lambda: next(inputs))

    # schowek (symulacja pyperclip)
    clipboard_content = {}
    monkeypatch.setattr(cli.pyperclip, "copy",
                        lambda value: clipboard_content.update({"last":
                                                                value}))

    # uruchomienie aplikacji w trybie testowym
    # cli.main(end=False)
    cli.main()

    # pobranie wyjścia z terminala
    captured = capsys.readouterr()

    # sprawdzenie, że ANSI dla koloru jest w wyjściu
    assert f"38;2;{r};{g};{b}m" in captured.out

    # sprawdzenie, że "fg" skopiowało poprawny kod do schowka
    assert clipboard_content["last"] == f"\033[38;2;{r};{g};{b}m"
