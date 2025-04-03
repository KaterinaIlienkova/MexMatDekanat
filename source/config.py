import logging

# Базове налаштування логування
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = "7946045090:AAGz4mbCcE_TC8CIcDuh4jQsgZgBSdGgi5g"

DB_CONFIG = {
    "user": "root",
    "password": "1234567",
    "host": "localhost",
    "port": 3306,
    "database": "mexmatbot"
}
