import requests
import json
import time
from datetime import datetime

from token_site import SCLAD_HEADERS
from token_site import OZON_HEADERS, ORGANIZATION_ID
from connect_Ozon_Sclad_productid import id_connect
# from check_status_order import ORDER_LIST

from loggirovanie import log_


def custom_lst():
    limit = 1000
    offset = 0
    with requests.Session() as session:
        params = {
            "limit": limit,
            "offset": offset,
        }
        url = "https://api.moysklad.ru/api/remap/1.2/entity/customerorder"
        try:
            req = requests.get(url=url, headers=SCLAD_HEADERS, params=params)

            stock_data = req.json()
            number_of_order = int(stock_data.get('rows')[0].get('name'))
            print(json.dumps(stock_data.get('rows'), indent=4, ensure_ascii=False))
            order_state = stock_data.get('rows')[0].get('state').get('meta').get('href').split('/')[-1]
            # print(order_state)
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при запросе: {e}")
            return None


custom_lst()
# print(custom_lst())
