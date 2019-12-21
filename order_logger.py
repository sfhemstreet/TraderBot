import logging
from logging import FileHandler
from logging import Formatter

LOG_FORMAT = ("%(asctime)s [%(levelname)s]: %(message)s")
LOG_LEVEL = logging.INFO

ORDER_LOG_FILE = "orders.log"

order_logger = logging.getLogger("traderbot_order.log")
order_logger.setLevel(LOG_LEVEL)

order_logger_file_handler = FileHandler(ORDER_LOG_FILE)
order_logger_file_handler.setLevel(LOG_LEVEL)
order_logger_file_handler.setFormatter(Formatter(LOG_FORMAT))

order_logger.addHandler(order_logger_file_handler)