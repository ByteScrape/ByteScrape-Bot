import logging
import re
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

import emoji
from colorama import Fore
from utils.config import Config

# Precompile emoji pattern for reuse
_EMOJI_PATTERN = re.compile(
    r"[\U0001F600-\U0001F64F"
    r"\U0001F300-\U0001F5FF"
    r"\U0001F680-\U0001F6FF"
    r"\U0001F1E0-\U0001F1FF"
    r"\U00002500-\U00002587"
    r"\U00002589-\U00002BEF"
    r"\U00002702-\U000027B0"
    r"\U000024C2-\U00002587"
    r"\U00002589-\U0001F251"
    r"\U0001f926-\U0001f937"
    r"\U00010000-\U0010ffff"
    r"\u2640-\u2642"
    r"\u2600-\u2B55"
    r"\u200d"
    r"\u23cf"
    r"\u23e9"
    r"\u231a"
    r"\ufe0f"
    r"\u3030"
    r"\u231b"
    r"\u2328"
    r"\u23ea"
    r"\u23eb"
    r"\u23ec"
    r"\u23ed"
    r"\u23ee"
    r"\u23ef"
    r"\u23f0"
    r"\u23f1"
    r"\u23f2"
    r"\u23f3]+",
    flags=re.UNICODE
)


def remove_emoji(string: str) -> str:
    return _EMOJI_PATTERN.sub(r"", string)


class CustomFormatter(logging.Formatter):
    def __init__(self, fmt, datefmt=None):
        super().__init__(fmt, datefmt)
        self.fmt = fmt
        self.datefmt = datefmt
        self.FORMATS = {
            logging.DEBUG: Fore.LIGHTCYAN_EX + fmt + Fore.RESET,
            logging.INFO: Fore.LIGHTYELLOW_EX + fmt + Fore.RESET,
            logging.WARNING: Fore.LIGHTRED_EX + fmt + Fore.RESET,
            logging.ERROR: Fore.LIGHTRED_EX + fmt + Fore.RESET,
            logging.CRITICAL: Fore.LIGHTRED_EX + fmt + Fore.RESET,
        }

    def format(self, record):
        if not hasattr(record, "emoji_is_present"):
            record.emoji_is_present = False

        if hasattr(record, "emoji"):
            record.msg = emoji.emojize(f"{record.emoji} {record.msg.strip()}")
            record.emoji_is_present = True

        if "\u2192" in record.msg:
            record.msg = record.msg.replace("\u2192", "-->")
            record.msg = remove_emoji(record.msg)

        # Choose the format for the current log level
        log_fmt = self.FORMATS.get(record.levelno, self.fmt)
        formatter = logging.Formatter(fmt=log_fmt, datefmt=self.datefmt)
        return formatter.format(record)


logger = logging.getLogger(Config().name)
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(
    CustomFormatter(fmt="%(asctime)s - %(levelname)s: %(message)s", datefmt="%d/%m/%y %H:%M:%S")
)


def save():
    logs_path = Path.cwd() / "logs"
    logs_path.mkdir(parents=True, exist_ok=True)

    # Use current date and time as the file name
    now_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    logs_file = logs_path / f"{now_str}.log"

    file_handler = TimedRotatingFileHandler(
        filename=str(logs_file),
        when="D",
        interval=1,
        backupCount=7,
        encoding="utf-8",
        delay=False
    )
    file_handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s - %(levelname)s: %(message)s",
            datefmt="%d/%m/%y %H:%M:%S"
        )
    )
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)


if Config().save_logs:
    save()

logger.addHandler(console_handler)
