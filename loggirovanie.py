import logging
import inspect
import os


def log_(func):
    """ Прописывание логов программы"""
    __name__ = 'main_log'
    func_name = inspect.currentframe().f_back.f_code.co_name

    frame = inspect.stack()[1].filename
    py_name = os.path.splitext(os.path.basename(frame))[0]  # Название файла без расширения

    # print(py_name, func_name, "FUNC")
    # получение пользовательского логгера и установка уровня логирования
    py_logger = logging.getLogger(__name__)
    py_logger.setLevel(logging.INFO)

    # настройка обработчика и форматировщика в соответствии с нашими нуждами
    py_handler = logging.FileHandler(f"{__name__}.log", mode='a', encoding='utf-8')
    py_formatter = logging.Formatter(f"%(asctime)s - {py_name.upper()} - {func_name} - %(levelname)s - %(message)s")

    # добавление форматировщика к обработчику
    py_handler.setFormatter(py_formatter)
    # добавление обработчика к логгеру
    py_logger.addHandler(py_handler)

    py_logger.info(func)
