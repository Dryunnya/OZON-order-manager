import requests
import json
from token_site import SCLAD_HEADERS


def get_stores():
    url = "https://api.moysklad.ru/api/remap/1.2/entity/store"
    try:
        response = requests.get(url, headers=SCLAD_HEADERS)
        response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)

        # Распарсиваем JSON ответ
        data = response.json()
        # print(json.dumps(data, indent=4, ensure_ascii=False))  # Выводим все данные для дебага
        return data
    except requests.exceptions.RequestException as e:
        error_message = f"Ошибка запроса: {e}"
        if 'response' in locals() and response is not None: #check that the response object exists
            error_message += f"\nStatus code: {response.status_code}"
            error_message += f"\nResponse text: {response.text}"
        return False, None, error_message

stores_data = get_stores()

if stores_data and 'rows' in stores_data: # Убедимся, что данные получены и содержат поле 'rows'
    for store in stores_data.get('rows'):
        store_id = store.get('id')
        store_name = store.get('name')
        print(f"ID склада: {store_id}, Название склада: {store_name}")