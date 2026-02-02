import requests
import json
import time
from token_site import OZON_HEADERS
from ozon_get import ALL_OZON_PRODUCTS
from sclad_get import ALL_SCLAD_PRODUCTS
from exceptions_test import handle_exceptions


# from loggirovanie import log_

@handle_exceptions
def update_ozon_stocks():
    """ Выгрузка остатков с Мой Склад на Ozon """
    with requests.Session() as session:
        sclad = ALL_SCLAD_PRODUCTS
        ozon = ALL_OZON_PRODUCTS
        sclad_articul = {product['артикул для ОЗОНА']: product for product in sclad}
        ozon_articul = {product['offer_id']: product for product in ozon}

        for offer_id, ozon_product in ozon_articul.items():
            if offer_id in sclad_articul:
                sclad_product = sclad_articul[offer_id]
                if sclad_product['Расчёт остатков'] is not None and sclad_product['stock'] > 1:

                    formula = sclad_product['Расчёт остатков']
                    available = sclad_product['available']
                    try:
                        formula = formula.replace('available', str(available))
                        formula = formula.replace('Nsklad',
                                                  str(int(
                                                      available)))  # Assuming Nsklad is a synonym for available. If not provide the mapping
                        available_stock = eval(formula)
                        available_stock = float(available_stock)
                    except (SyntaxError, NameError, TypeError) as e:
                        print(f"Error: Could not evaluate formula for offer_id {offer_id}: {formula}. {e}")
                else:
                    available_stock = sclad_product['available']
                available_stok = max(0, int(available_stock))
                # print(available_stok)

                url = 'https://api-seller.ozon.ru/v2/products/stocks'
                data = {"stocks": [
                    {
                        "offer_id": offer_id,
                        "product_id": int(ozon_product['product_id']),
                        "quant_size": 1,
                        "stock": available_stok,
                        # "warehouse_id": 1020001331027000  # вилсмаркет
                        "warehouse_id": 1020005000054807  # кантрипулс

                    }
                ]
                }
                req = requests.Request('POST', url, headers=OZON_HEADERS, data=json.dumps(data))

                # call function of logging
                # log_(f"{req} - {url}")

                prepped = session.prepare_request(req)
                response = session.send(prepped)
                response.raise_for_status()
                time.sleep(1)


if __name__ == "__main__":
    print(json.dumps(update_ozon_stocks(), indent=4, ensure_ascii=False))
