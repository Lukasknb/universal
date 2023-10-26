import logging.config
import os
from datetime import datetime

if os.getenv("LOGGING_LEVEL"):
    log_level = os.getenv("LOGGING_LEVEL")
else:
    log_level = "INFO"


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


def _get_list_from_env(prefix: str):
    """
    Retrieves a list from environment variables using a specified prefix.

    Args:
        prefix (str): The prefix used to store the list items in the environment variables.

    Returns:
        list: The reconstructed list from the environment variables.
    """
    data_list = []
    index = 0
    while True:
        env_var_name = f"{prefix}_{index}"
        if env_var_name in os.environ:
            data_list.append(os.environ[env_var_name])
            index += 1
        else:
            break
    return data_list


LOGGING_FILTER = _get_list_from_env("LOGGING_FILTER")


class LoggingFilter(logging.Filter):
    def filter(self, record):
        if record.name in LOGGING_FILTER:
            return False
        return True


# Dynamic log file path for bundled and non-bundled applications
LOG_BASEPATH = os.environ.get("BASE_PATH") if os.environ.get(
    "BASE_PATH") else os.path.dirname(os.path.dirname(__file__))  # Base path contains the path of the bundled application or root directory of the non-bundled application
LOG_FOLDER = 'logs' if not os.getenv(
    "LOGGING_DIRECTORY") else os.getenv("LOGGING_DIRECTORY")
LOG_DIRECTORY = os.path.join(LOG_BASEPATH, LOG_FOLDER)
LOG_FILENAME = datetime.now().strftime('%Y-%m-%d') + ".log"
LOG_FILE_PATH = os.path.join(LOG_DIRECTORY, LOG_FILENAME)


def ensure_log_directory_exists():
    if not os.path.exists(LOG_DIRECTORY):
        os.makedirs(LOG_DIRECTORY)
    elif os.path.exists(LOG_FILE_PATH):
        current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(LOG_FILE_PATH, 'a') as log_file:
            log_file.write(f"---------- {current_timestamp} ----------\n")
            log_file.write(f"---------- APPLICATION ----------\n")


ensure_log_directory_exists()


# Conditional format based on LOG_LEVEL
if log_level == 'DEBUG':
    log_format = '%(asctime)s [%(levelname)s] %(module)s.%(funcName)s | %(name)s: %(message)s'
else:
    log_format = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'


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
            '()': ColoredFormatter if os.environ.get("LOGGING_COLORED") == "True" else logging.Formatter,
            'format': log_format
        },
        'standard': {
            'format': log_format
        },
    },
    'handlers': {
        'default': {
            'level': log_level,
            'formatter': 'colored',
            'class': 'logging.StreamHandler',
            'filters': ['websockets_filter'],
        },
        'file': {
            'level': log_level,
            'formatter': 'standard',
            'class': 'logging.FileHandler',
            'filename': LOG_FILE_PATH,
            'mode': 'a',
            'filters': ['websockets_filter'],
        },
    },
    'loggers': {
        '': {
            'handlers': ['default', 'file'],
            'level': log_level,
            'propagate': True
        }
    }
}

logging.config.dictConfig(LOGGING_CONFIG)


def get_logger(name=None):
    return logging.getLogger(name if name else __name__)


def set_log_level(logger, level):
    """
    Set the log level of the root logger.
    """
    logging.getLogger().setLevel(logging.INFO)
