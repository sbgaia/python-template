from project_name.greeter import Greeter

if __name__ == "__main__":
    # Example usage within the project template
    user_name = input("Enter your name: ")
    user_language: str = input(
        "Enter your language code (e.g., en, es, fr): "
    ).upper()

    greeter = Greeter(user_name, user_language)
    print(greeter.greet())
