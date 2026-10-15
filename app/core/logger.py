import sys
from collections import deque
from loguru import logger

ui_log_queue = deque(maxlen=100)

def ui_sink(message):
    ui_log_queue.append(message.record["message"]) 

logger.remove()
logger.add(sys.stdout, level="DEBUG")
logger.add("logs/system.log", rotation="10 MB", level="INFO")
logger.add(ui_sink, level="INFO", format="{time:HH:mm:ss} | {level} | {message}")

system_logger = logger