import logging
from enum import Enum
from typing import ClassVar

# Configure logging
logging.basicConfig(
    level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s"
)


class Language(Enum):
    """Supported languages for the greeter class."""

    EN = "English"
    ES = "Spanish"
    FR = "French"
    DE = "German"
    IT = "Italian"
    PT = "Portuguese"
    ZH = "Chinese"
    JA = "Japanese"


def get_language(language: str | Language) -> Language:
    """Get the corresponding language code from the Language enum.

    Args:
        language (str | Language): The language code as a string or
            `Language` enum.

    Returns:
        Language: The corresponding Language enum member.
    """
    if isinstance(language, Language):
        return language

    # find the language code in the Language enum
    for lang in Language:
        if lang.name == language.upper():
            return lang
    logging.error(
        f"Unsupported language code: {language}, defaulting to English."
    )
    return Language.EN


class Greeter:
    """A simple greeter class that supports multiple languages."""

    GREETINGS: ClassVar[dict[Language, str]] = {
        Language.EN: "Hello",
        Language.ES: "Hola",
        Language.FR: "Bonjour",
        Language.DE: "Hallo",
        Language.IT: "Ciao",
        Language.PT: "Olá",
        Language.ZH: "你好",
        Language.JA: "こんにちは",
    }

    def __init__(
        self, name: str, language: str | Language = Language.EN
    ) -> None:
        """Initialize the Greeter with a name and an optional language.

        Args:
            name (str): The name of the person to greet.
            language (str | Language, optional): The language code for the
                greeting. Defaults to `Language.EN`.
        """
        self.name = name
        self.language = get_language(language)

    def greet(self) -> str:
        """Return a greeting message in the specified language.

        Returns:
            str: The greeting message.
        """
        return f"{self.GREETINGS[self.language]}, {self.name}!"
