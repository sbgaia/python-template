# SPDX-FileCopyrightText: 2026 the Python Template contributors
#
# SPDX-License-Identifier: BSD-2-Clause

import pytest

from project_name.greeter import Greeter, Language, get_language


@pytest.mark.parametrize(
    "language, expected_greeting",
    [
        (Language.EN, "Hello, {name}!"),
        (Language.ES, "Hola, {name}!"),
        (Language.FR, "Bonjour, {name}!"),
        (Language.DE, "Hallo, {name}!"),
        (Language.IT, "Ciao, {name}!"),
        (Language.PT, "Olá, {name}!"),
        (Language.ZH, "你好, {name}!"),
        (Language.JA, "こんにちは, {name}!"),
    ],
)
class TestGreeter:
    def test_greet(self, language: Language, expected_greeting: str) -> None:
        # Arrange
        name = "Mario"

        # Act
        greeter = Greeter(name, language)

        # Assert
        assert greeter.greet() == expected_greeting.format(name=name)


def test_get_language_accepts_string_code() -> None:
    assert get_language("it") is Language.IT


def test_get_language_defaults_to_english_for_unsupported_code(
    caplog: pytest.LogCaptureFixture,
) -> None:
    assert get_language("xx") is Language.EN
    assert "Unsupported language code: xx" in caplog.text
