from telegram import Update
from telegram.ext import CallbackContext

from source.auth.registration import confirm
from source.courses.handlers import view_courses_by_student, view_students, courses
from source.documents.handlers import doc_request, doc_requested
from source.faq.handlers import send_qa, show_edit_qa_options
from source.announcements.publication import sent_publication

async def send_instructions(update: Update, context: CallbackContext):
    """Надсилає інструкції користувачеві."""
    await update.message.reply_text("Список команд:\n/start - Початок роботи\n/register - Реєстрація користувача\n/help - Допомога")

async def handle_button_click(update: Update, context: CallbackContext):
    """Обробляє натискання кнопок на клавіатурі."""
    text = update.message.text

    if text == "Інструкції":
        await send_instructions(update, context)
    elif text == "Додати користувача":
        from source.auth.registration import prompt_user_details
        await prompt_user_details(update, context)
    elif text == "Q&A":
        await send_qa(update, context)  # Викликаємо список питань
    elif text == "Редагувати Q&A":
        await show_edit_qa_options(update, context)  # Опції редагування Q&A
    elif text == "Оголошення":
        await sent_publication(update, context)  # Ініціювання публікації оголошення
    elif text == "Підтвердити реєстрацію":
        await confirm(update, context)
    elif text == "Мої поточні курси":
        await view_courses_by_student(update, context)
    elif text == "Списки студентів":
        await view_students(update, context)
    elif text == "Замовити документ":
        await doc_request(update, context)
    elif text == "Заявки на документи":
        await doc_requested(update, context)  # Працівник деканату ініціює перегляд заявок на отримання документів
    elif text == "Курси":
        await courses(update, context)