import pytest

from project_name.greeter import Greeter, Language


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
