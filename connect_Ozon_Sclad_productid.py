from ozon_get import ALL_OZON_PRODUCTS
from sclad_get import ALL_SCLAD_PRODUCTS


def id_connect():
    ''' Сращивает товары из ozon с Мой склад.
    Создаёт словарь, ключем которого является offer_id, а значения словаря - это вся информация по товару.
    Этот словарь мы передаём в check_status_order'''
    sclad = ALL_SCLAD_PRODUCTS
    ozon = ALL_OZON_PRODUCTS

    sclad_articul = {product['артикул для ОЗОНА']: product for product in sclad}
    ozon_articul = {product['offer_id']: product for product in ozon}

    PROD_OFFER_DCT = {}

    for offer_id, ozon_product in ozon_articul.items():
        if offer_id in sclad_articul:
            PROD_OFFER_DCT[offer_id] = sclad_articul[offer_id]
    return PROD_OFFER_DCT


if __name__ == '__main__':
    id_con = id_connect()
    print(id_con)
