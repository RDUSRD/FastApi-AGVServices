import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from zoneinfo import ZoneInfo  # Disponible en Python 3.9+

# Configurar la zona horaria deseada
TIMEZONE = "America/Caracas"  # Cambia esta cadena por la zona horaria que necesites

# Crear la carpeta de logs, si no existe
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

class CustomFormatter(logging.Formatter):
    """
    Formateador personalizado que añade información extra si no se proporciona.
    Se espera que cada registro tenga los campos 'device', 'user' e 'ip'.
    """
    def format(self, record):
        if not hasattr(record, 'device'):
            record.device = "UnknownDevice"
        if not hasattr(record, 'user'):
            record.user = "UnknownUser"
        if not hasattr(record, 'ip'):
            record.ip = "UnknownIP"
        if not hasattr(record, 'custom_func'):
            record.custom_func = record.funcName
        return super().format(record)

def get_logger(logger_name: str):
    """
    Configura un logger con RotatingFileHandler que rota los archivos cuando alcanzan 10 MB y guarda hasta 5 backups.
    El formato de cada registro es:
    Time: %(asctime)s | Level: %(levelname)s | Device: %(device)s | User: %(user)s | IP: %(ip)s | Func: %(funcName)s | Msg: %(message)s
    """
    now_tz = datetime.now(ZoneInfo(TIMEZONE))
    date_str = now_tz.strftime("%Y-%m-%d")
    log_file = os.path.join(LOG_DIR, f"{date_str}.log")

    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

    format_str = "Time: %(asctime)s | Level: %(levelname)s | Device: %(device)s | User: %(user)s | IP: %(ip)s | Func: %(custom_func)s | Msg: %(message)s"
    formatter = CustomFormatter(format_str)
    formatter.converter = lambda *args: datetime.now(ZoneInfo(TIMEZONE)).timetuple()

    handler = RotatingFileHandler(log_file, maxBytes=10 * 1024 * 1024, backupCount=5)
    handler.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(handler)

    return logger