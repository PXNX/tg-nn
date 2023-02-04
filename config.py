import os
from dotenv import load_dotenv

load_dotenv()

CHANNEL_TEST=-1001391125365
CHANNEL_BACKUP =  -1001861018052

DEEPL=os.getenv("DEEPL")
DATABASE_URL=os.getenv("DATABASE_URL")