# utils.py
import json
import logging
import os
import time
import datetime
import asyncio
from functools import wraps
from typing import Any, Callable, Dict, Optional


# =============================
# LOGGING CONFIGURATION
# =============================

def setup_logger(name: str = "trading_bot", log_file: str = "trading.log", level=logging.INFO) -> logging.Logger:
    """
    Set up a logger that writes to both file and console.
    """
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S")

    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)

    console = logging.StreamHandler()
    console.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        logger.addHandler(handler)
        logger.addHandler(console)

    return logger


logger = setup_logger()


# =============================
# CONFIGURATION LOADER
# =============================

def load_config(file_path: str = "config.json") -> Dict[str, Any]:
    """
    Load configuration settings from a JSON file.
    """
    if not os.path.exists(file_path):
        logger.warning(f"Config file {file_path} not found. Using defaults.")
        return {}
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding config file: {e}")
        return {}


# =============================
# TIME UTILITIES
# =============================

def now() -> str:
    """
    Get the current UTC time as an ISO string.
    """
    return datetime.datetime.utcnow().isoformat()


def sleep(seconds: float):
    """
    Simple sleep wrapper with logging.
    """
    logger.debug(f"Sleeping for {seconds} seconds...")
    time.sleep(seconds)


# =============================
# PRICE & VALUE HELPERS
# =============================

def round_price(price: float, step: float) -> float:
    """
    Round price to the nearest allowed tick size (exchange precision).
    """
    return round(price / step) * step


def clamp(value: float, min_val: float, max_val: float) -> float:
    """
    Clamp a number between min and max.
    """
    return max(min_val, min(max_val, value))


# =============================
# RETRY & ERROR HANDLING
# =============================

def retry(max_attempts: int = 3, delay: float = 2.0, exceptions=(Exception,)):
    """
    Retry a function upon exception.
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    logger.warning(f"{func.__name__} failed: {e}. Attempt {attempt + 1}/{max_attempts}")
                    if attempt < max_attempts - 1:
                        time.sleep(delay)
                    else:
                        raise
        return wrapper
    return decorator


# =============================
# ASYNC HELPERS
# =============================

async def async_retry(func: Callable, *args, retries: int = 3, delay: float = 1.0, **kwargs):
    """
    Async version of retry logic.
    """
    for attempt in range(retries):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.warning(f"Async {func.__name__} failed: {e}. Attempt {attempt + 1}/{retries}")
            if attempt < retries - 1:
                await asyncio.sleep(delay)
            else:
                raise


# =============================
# MISCELLANEOUS UTILITIES
# =============================

def percentage_change(old: float, new: float) -> float:
    """
    Calculate the percentage change between two prices.
    """
    if old == 0:
        return 0.0
    return ((new - old) / old) * 100.0


def safe_get(d: Dict[str, Any], key: str, default: Any = None) -> Any:
    """
    Safe dictionary getter with default value.
    """
    return d[key] if key in d else default


def format_currency(amount: float, currency: str = "USD") -> str:
    """
    Format amount as a currency string.
    """
    return f"{amount:,.2f} {currency}"


def timestamp_ms() -> int:
    """
    Returns current timestamp in milliseconds.
    """
    return int(time.time() * 1000)


def log_error(message: str, exc: Exception | None = None):
    """
    Unified error logging helper.
    Logs to both console and file using the global logger.
    """
    if exc:
        logger.error(f"{message} | Exception: {exc}")
        print(f"❌ {message}: {exc}")
    else:
        logger.error(message)
        print(f"❌ {message}")
