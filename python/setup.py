"""
setup.py

This file is executed on import to setup the application. Meant to be imported first in main.py.

Notes:
    - Sets execution and base path as environment variables
    - Attempts to load config from config.yaml into environment variables
        - If config.yaml does not exist, sets FIRST_RUN to "True" (Application needs to handle fist setup)
    - Configures terminal to use color coded output if possible

    - Requires: PyYAML, colorama
"""
import os
import sys
import ctypes
import yaml
import logging
import logging.config
from datetime import datetime


def steup_temp_logger():
    log_level = 'INFO'
    log_format = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'

    LOG_DIRECTORY = 'logs'
    LOG_FILENAME = datetime.now().strftime('%Y-%m-%d') + ".log"
    LOG_FILE_PATH = os.path.join(LOG_DIRECTORY, LOG_FILENAME)

    # Ensure log directory exists
    if not os.path.exists(LOG_DIRECTORY):
        os.makedirs(LOG_DIRECTORY)
    elif os.path.exists(LOG_FILE_PATH):
        with open(LOG_FILE_PATH, 'a') as log_file:
            log_file.write(
                f"---------- {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ----------\n")
            log_file.write(f"---------- SETUP ----------\n")

    LOGGING_CONFIG = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'colored': {
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
            },
            'file': {
                'level': log_level,
                'formatter': 'standard',
                'class': 'logging.FileHandler',
                'filename': LOG_FILE_PATH,
                'mode': 'a',
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
    return logging.getLogger("SETUP")


def setup():
    logger = steup_temp_logger()
    logger.info("Starting setup")
    base_path, exe_path = get_paths()
    os.environ["BASE_PATH"] = base_path
    os.environ["EXE_PATH"] = exe_path

    loaded = load_config(
        os.path.join(exe_path + "/config.yaml"),
        logger=logger)

    if not loaded and os.environ.get("FIRST_RUN") != "True":
        logging.error("Config could not be loaded")
        os.environ["SETUP_SUCCESS"] = "False"
        logger.warning("Setup could not be completed")
        return
    elif os.environ.get("FIRST_RUN") == "True":
        # Application needs to run setup routine
        pass

    # Attempt to enable VT processing. If not successful, use colorama as a fallback.
    if not enable_virtual_terminal_processing(logger=logger):
        try:
            from colorama import init
            init(autoreset=True)
            logger.info("Colorama enabled for console")
            os.environ["LOGGING_COLORED"] = "True"
        except ImportError:
            logger.warning(
                "Virtual processing and colorama not enabled, console will default to plain text")
            os.environ["LOGGING_COLORED"] = "False"

    os.environ["SETUP_SUCCESS"] = "True"
    logger.info("Setup complete")


def get_paths() -> tuple[str, str]:
    """
    Returns the base path and the executable path of the application.

    Returns:
        tuple[str, str]: The base path and the executable path of the application.
    """
    # Get the base path of the application depending on whether it is bundled or not
    if getattr(sys, 'frozen', False):
        # The application is bundled
        base_path = sys._MEIPASS
        exe_path = os.path.dirname(os.path.abspath(sys.executable))
    else:
        # The application is not bundled
        base_path = os.path.dirname(os.path.abspath(__file__))
        exe_path = base_path

    return base_path, exe_path


def enable_virtual_terminal_processing(logger: logging.Logger = logging.getLogger(__name__)):
    # Check for Windows platform
    if os.name == "nt":
        # Check for Windows version 10.0.14393 and above as they support ANSI escape sequences
        windows_version = sys.getwindowsversion()
        if windows_version.major >= 10 and windows_version.build >= 14393:
            kernel32 = ctypes.windll.kernel32
            hOut = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
            mode = ctypes.c_ulong()
            kernel32.GetConsoleMode(hOut, ctypes.byref(mode))
            mode.value |= 4  # ENABLE_VIRTUAL_TERMINAL_PROCESSING
            logger.info("Virtual terminal processing enabled")
            os.environ["LOGGING_COLORED"] = "True"
            return kernel32.SetConsoleMode(hOut, mode)
    logger.warning(
        "Virtual terminal processing not enabled, colorama will be used as a fallback")
    return False


def load_config(path_to_config: str, logger: logging.Logger = logging.getLogger(__file__)) -> bool:
    """
    Loads the config into the environment variables

    Args:
        path_to_config (str): path to the config file

    Returns:
        bool: True if the config was loaded successfully, False otherwise
    """
    logger.info("Attempting to load config")
    if not os.path.exists(path_to_config):
        os.environ["FIRST_RUN"] = "True"
        logger.warning("Config file does not exist, assuming first run")
        return False
    os.environ["FIRST_RUN"] = "False"
    with open(path_to_config, 'r') as stream:
        try:
            data = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            logger.error(exc)
            logger.info("Config could not be loaded. Please make sure the config file is valid."
                        "Optionally, delete the config file to generate a new one on next startup.")
            return False

    logger.info("Config loaded, setting environment variables")
    set_env_vars(data)

    if os.environ.get('LOGGING_LEVEL'):
        try:
            logger.setLevel(os.environ.get('LOGGING_LEVEL'))
        except ValueError:
            logger.error("Invalid logging level: %s",
                         os.environ.get('LOGGING_LEVEL'))
            return False

    return True


def set_env_vars(data, prefix=""):
    """
    Recursively traverses the config to build the name of the environment variable and set it

    Args:
        data (dict or list): the config data
        prefix (str): the prefix of the environment variable from the previous iteration
    """
    if isinstance(data, dict):
        for key, value in data.items():
            new_prefix = f"{prefix}_{key.upper()}" if prefix else key.upper()
            set_env_vars(value, new_prefix)
    elif isinstance(data, list):
        for index, value in enumerate(data):
            new_prefix = f"{prefix}_{index}" if prefix else str(index)
            set_env_vars(value, new_prefix)
    else:
        os.environ[prefix] = str(data)


setup()
