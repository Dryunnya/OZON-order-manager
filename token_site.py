import requests
import json
import os
from exceptions_test import handle_exceptions

# from loggirovanie import log_
""" Токены систем и их headers """

TOKEN_FILE = "tokens_of_sites.textmate"
token_names = ["OZON_TOKEN", "CLIENT_ID", "MY_SCLAD_TOKEN"]

# Правки
''' Прописать возможность добавления токенов нескольки компаний при первом запуске программы
При повторном запуске программа запускается в автоатическом формате для каждой из компаний, подставляя токены и 
id контрагента (уже реализовано). Если файл уже создан, то программа просто читает все токены и запускается для каждой из них (не закрываясь).
Добавить файл описания программы README. Создать новую открытую директорию на гитхабе, предварительно удалив все токены.'''


def read_tokens_from_console():
    """Читает токены из консоли."""
    tokens = {}
    for token_name in token_names:
        print(f"Пожалуйста, введите {token_name}:")
        token_value = input().strip()
        tokens[token_name] = token_value
    return tokens


def save_tokens_to_file(tokens):
    """Сохраняет токены в текстовый файл.  Каждый токен на новой строке."""
    try:
        with open(TOKEN_FILE, "w") as f:
            for key, value in tokens.items():
                f.write(f"{key}={value}\n")  # Save as key=value pairs, one per line
        file_to_dict(TOKEN_FILE)
        print(f"Токены сохранены в файл: {TOKEN_FILE}")
    except Exception as e:
        print(f"Ошибка при записи токенов в файл: {e}")


def read_tokens_from_file():
    """Читает токены из текстового файла."""
    try:
        tokens = {}
        with open(TOKEN_FILE, "r") as f:
            for line in f:
                line = line.strip()  # Remove leading/trailing whitespace
                if line:  # Ignore empty lines
                    key, value = line.split("=", 1)  # Split into key and value at the first '='
                    tokens[key] = value
        return tokens
    except FileNotFoundError:
        return {}  # Возвращаем пустой словарь, если файл не найден
    except Exception as e:
        print(f"Ошибка при чтении токенов из файла: {e}")
        return {}


def file_to_dict(file_name):  # функция из файла в словарь
    with open(file_name, encoding='utf8') as file:  # Читаем файл
        lines = file.read().splitlines()  # read().splitlines() - чтобы небыло пустых строк
    dic = {}  # Создаем пустой словарь
    for line in lines:  # Проходимся по каждой строчке
        key, value = line.split(
            '=')  # Разделяем каждую строку по символу равно(в key будет - переменная, в value - значение)
        dic.update({key: value})  # Добавляем в словарь
    return dic


def get_all_tokens():
    """
    Получает все токены. Если файл не существует, читает токены из консоли и сохраняет их в файл.
    В противном случае читает токены из файла.
    """
    if not os.path.exists(TOKEN_FILE):
        # Файл не существует, читаем из консоли и сохраняем
        tokens = read_tokens_from_console()
        save_tokens_to_file(tokens)
    else:
        # Файл существует, читаем из файла
        tokens = read_tokens_from_file()  # или file_to_dict(TOKEN_FILE)
    return tokens


all_tok = get_all_tokens()
OZON_TOKEN = all_tok.get('OZON_TOKEN')
CLIENT_ID = all_tok.get('CLIENT_ID')
MY_SCLAD_TOKEN = all_tok.get('MY_SCLAD_TOKEN')

OZON_HEADERS = {
    'Host': 'api-seller.ozon.ru',
    'Client-Id': f'{CLIENT_ID}',
    'Api-Key': f'{OZON_TOKEN}',
    'Content-Type': 'application/json'
}

SCLAD_HEADERS = {'Authorization': f'Bearer {MY_SCLAD_TOKEN}', 'Content-Type': 'application/json'}


@handle_exceptions
def contragent_info():
    '''id контр-агента'''
    with requests.Session() as session:
        url = "https://api.moysklad.ru/api/remap/1.2/entity/counterparty"
        req = requests.Request('GET', url, headers=SCLAD_HEADERS)
        prepped = session.prepare_request(req)
        response = session.send(prepped)
        response.raise_for_status()
        response_json = response.json()
        # print(json.dumps(response_json.get('rows'), indent=4, ensure_ascii=False))
        for elem in response_json.get('rows'):
            if elem.get('name') == "ОЗОН":
                return elem.get('id')


COUNTERPARTY_ID = contragent_info()


# print(COUNTERPARTY_ID)

@handle_exceptions
def organizations_info():
    """ Извлечение всей информации о компании (в данной ф-ции вытаскиваем organization_id) """
    with requests.Session() as session:
        url = 'https://api.moysklad.ru/api/remap/1.2/entity/organization'
        req = requests.Request('GET', url, headers=SCLAD_HEADERS)
        prepped = session.prepare_request(req)
        response = session.send(prepped)
        response.raise_for_status()
        response_json = response.json()
        return response_json.get('rows')


ORGANIZATION_ID = ''
org_data = organizations_info()

if org_data:  # Ensure we have data before looping
    for org in org_data:
        if org.get('name') == 'ООО "КАНТРИПУЛС"':
            # if org.get('name') == 'ООО "ВИЛС МАРКЕТ"':
            ORGANIZATION_ID = org.get("id")  # use current `org` not the first element
            print(ORGANIZATION_ID)
            break  # break the loop after finding the correct organization
    else:
        print("Organization 'ООО \"КАНТРИПУЛС\"' not found.")
        # print("Organization 'ООО \"ВИЛС МАРКЕТ\"' not found.")
else:
    print("Could not retrieve organization data.")
