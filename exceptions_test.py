import requests
import json


def handle_exceptions(func):
    """
    Декоратор для обработки исключений в функциях.
    """

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при выполнении функции {func.__name__}: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"Ошибка декодирования JSON в функции {func.__name__}: {e}")
            return None
        except Exception as e:
            print(f"Непредвиденная ошибка в функции {func.__name__}: {e}")
            return None

    return wrapper
