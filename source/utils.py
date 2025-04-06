from telegram import Update
from telegram.ext import CallbackContext

from source.announcements.publication import send_announcement
from source.auth.permissions import handle_button_click
from source.auth.registration import save_new_user
from source.config import (WAITING_FOR_QUESTION, WAITING_FOR_ANSWER, WAITING_FOR_EDIT_ANSWER,
                           WAITING_FOR_ANNOUNCEMENT_TEXT, WAITING_FOR_USER_ROLE, WAITING_FOR_USER_DETAILS)
from source.database import SessionLocal
from source.faq.handlers import add_faq, update_faq


async def message_handler(update: Update, context: CallbackContext):
    """Обробляє текстові повідомлення залежно від стану розмови."""

    if update.message.text == "/cancel":
        context.user_data.clear()
        await update.message.reply_text("❌ Дію скасовано.")
        return

    state = context.user_data.get("state")

    # ✅ Додавання нового користувача: вибір ролі
    if state == WAITING_FOR_USER_ROLE:
        role = update.message.text.lower()
        if role not in ["student", "teacher"]:
            await update.message.reply_text("❌ Некоректна роль! Виберіть 'student' або 'teacher'.")
            return

        context.user_data["new_role"] = role
        context.user_data["state"] = WAITING_FOR_USER_DETAILS

        if role == "student":
            await update.message.reply_text("✏️ Введіть ім'я користувача, TelegramTag, номер телефону, групу, рік вступу та спеціальність через кому.\n\n📌 Приклад: Іван Петренко, ivan_petrenko, +380961234567, ФІ-21, 2023, Комп'ютерні науки")
        else:  # Викладач
            await update.message.reply_text("✏️ Введіть ім'я користувача, TelegramTag, номер телефону, email та кафедру через кому.\n\n📌 Приклад: Петро Іванов, petro_ivanov, +380501234567, petro@example.com, Кафедра математики")
        return

    # ✅ Додавання нового користувача: введення даних
    elif state == WAITING_FOR_USER_DETAILS:
        data = update.message.text.split(",")

        role = context.user_data["new_role"]
        if role == "student" and len(data) != 6:
            await update.message.reply_text("❌ Неправильний формат! Введіть 6 параметрів через кому.")
            return
        if role == "teacher" and len(data) != 5:  # Тепер очікуємо 5 параметрів для викладача
            await update.message.reply_text("❌ Неправильний формат! Введіть 5 параметрів через кому.")
            return

        context.user_data["new_user_name"] = data[0].strip()
        context.user_data["new_telegram_tag"] = data[1].strip()
        context.user_data["new_phone"] = data[2].strip()

        if role == "student":
            context.user_data["new_group"] = data[3].strip()
            context.user_data["new_admission_year"] = int(data[4].strip())
            context.user_data["new_specialty"] = data[5].strip()
        else:  # Викладач
            context.user_data["new_email"] = data[3].strip()  # Email - четвертий параметр
            context.user_data["new_department"] = data[4].strip()  # Кафедра - п'ятий параметр

        await save_new_user(update, context)
        return

    # Інші стани (FAQ, Оголошення тощо)
    elif state == WAITING_FOR_QUESTION:
        context.user_data["new_question"] = update.message.text
        context.user_data["state"] = WAITING_FOR_ANSWER
        await update.message.reply_text("✏️ Тепер введіть відповідь:")
        return

    elif state == WAITING_FOR_ANSWER:
        question = context.user_data.get("new_question", "")
        answer = update.message.text
        with SessionLocal() as db:
            success = add_faq(db, question, answer)
        if success:
            await update.message.reply_text("✅ Питання додано до FAQ!")
        else:
            await update.message.reply_text("❌ Помилка при додаванні питання.")
        context.user_data.clear()
        return

    elif state == WAITING_FOR_EDIT_ANSWER:
        faq_id = context.user_data.get("edit_faq_id")
        new_answer = update.message.text
        with SessionLocal() as db:
            success = update_faq(db, faq_id, new_answer)
        if success:
            await update.message.reply_text("✅ Відповідь оновлено!")
        else:
            await update.message.reply_text("❌ Помилка при оновленні.")
        context.user_data.clear()
        return

    elif state == WAITING_FOR_ANNOUNCEMENT_TEXT:
        announcement_text = update.message.text
        await send_announcement(update, context)
        return

    # Обробка кнопок
    await handle_button_click(update, context)
