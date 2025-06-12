import os
from datetime import datetime
from typing import Final

from dotenv import load_dotenv

load_dotenv()

CHANNEL_TEST = -1001391125365
CHANNEL_BACKUP = -1001861018052
GROUP_SOURCE = 1723195485  # requires pattern topic
GROUP_PATTERN = -1001895734902
GROUP_LOG = -1001723195485

CHANNEL_UA = -1001839268196

DEEPL = os.getenv("DEEPL")
DATABASE_URL = os.getenv("DATABASE_URL")
PASSWORD = os.getenv("PASSWORD")

TESTING = False
LOG_FILENAME = rf"./logs/{datetime.now().strftime('%Y-%m-%d/%H-%M-%S')}.log"

CONTAINER: Final[bool] = bool(os.getenv('CONTAINER', False), )

RES_PATH: Final[str] = "./res"