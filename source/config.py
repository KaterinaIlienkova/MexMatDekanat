import logging

# Базове налаштування логування
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Константи для станів розмови
WAITING_FOR_QUESTION = "waiting_for_question"
WAITING_FOR_ANSWER = "waiting_for_answer"
WAITING_FOR_EDIT_ANSWER = "waiting_for_edit_answer"
WAITING_FOR_ANNOUNCEMENT_TEXT = "waiting_for_announcement_text"
WAITING_FOR_USER_ROLE = "waiting_for_user_role"  # Очікування вибору ролі (студент/викладач)
WAITING_FOR_USER_DETAILS = "waiting_for_user_details"  # Очікування введення даних нового користувача
WAITING_FOR_STUDENT_DETAILS = "waiting_for_student_details"



BOT_TOKEN = "7946045090:AAGz4mbCcE_TC8CIcDuh4jQsgZgBSdGgi5g"

DB_CONFIG = {
    "user": "root",
    "password": "1234567",
    "host": "localhost",
    "port": 3306,
    "database": "mexmatbot"
}
