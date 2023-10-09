import logging.config
import os
from datetime import datetime

LOG_LEVEL = 'DEBUG'
FILTER = ['websockets.server', 'websockets.client']


class ColoredFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': '\033[94m',
        'INFO': '\033[92m',
        'WARNING': '\033[93m',
        'ERROR': '\033[91m',
        'CRITICAL': '\033[91m',
        'RESET': '\033[0m'
    }

    def format(self, record):
        log_message = super().format(record)
        return f"{self.COLORS.get(record.levelname, self.COLORS['RESET'])}{log_message}{self.COLORS['RESET']}"


class LoggingFilter(logging.Filter):
    def filter(self, record):
        if record.name in FILTER:
            return False
        return True


LOG_DIRECTORY = 'logs'
LOG_FILENAME = datetime.now().strftime('%Y-%m-%d') + ".log"
LOG_FILE_PATH = os.path.join(LOG_DIRECTORY, LOG_FILENAME)


def ensure_log_directory_exists():
    if not os.path.exists(LOG_DIRECTORY):
        os.makedirs(LOG_DIRECTORY)
    elif os.path.exists(LOG_FILE_PATH):
        current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(LOG_FILE_PATH, 'a') as log_file:
            log_file.write(f"---------- {current_timestamp} ----------\n")


ensure_log_directory_exists()


LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'websockets_filter': {
            '()': LoggingFilter,
        },
    },
    'formatters': {
        'colored': {
            '()': ColoredFormatter,
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level': LOG_LEVEL,
            'formatter': 'colored',
            'class': 'logging.StreamHandler',
            'filters': ['websockets_filter'],
        },
        'file': {
            'level': LOG_LEVEL,
            'formatter': 'standard',  # Use the plain formatter for file logs
            'class': 'logging.FileHandler',
            'filename': LOG_FILE_PATH,
            'mode': 'a',
            'filters': ['websockets_filter'],
        },
    },
    'loggers': {
        '': {
            'handlers': ['default', 'file'],
            'level': LOG_LEVEL,
            'propagate': True
        }
    }
}

logging.config.dictConfig(LOGGING_CONFIG)


def get_logger(name=None):
    return logging.getLogger(name if name else __name__)

