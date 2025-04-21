from sqlalchemy.exc import SQLAlchemyError
from telegram import Update
from telegram.ext import CallbackContext

from source.announcements.publication import send_announcement
from source.auth.permissions import handle_button_click
from source.auth.registration import save_new_user, confirm_command, edit_user_handler
from source.config import (WAITING_FOR_QUESTION, WAITING_FOR_ANSWER, WAITING_FOR_EDIT_ANSWER,
                           WAITING_FOR_ANNOUNCEMENT_TEXT, WAITING_FOR_USER_ROLE, WAITING_FOR_USER_DETAILS,
                           WAITING_FOR_STUDENT_DETAILS, WAITING_FOR_SCAN_LINK, WAITING_FOR_EDIT_FIELD)
from source.courses.db_queries import get_teacher_id_by_username, add_new_course
from source.courses.handlers import ADD_COURSE_LINK, ADD_COURSE_PLATFORM, ADD_COURSE_NAME, courses
from source.database import SessionLocal
from source.faq.handlers import add_faq, update_faq
from source.models import DocumentRequest, Student, User, StudentGroup
import logging
logger = logging.getLogger(__name__)

async def message_handler(update: Update, context: CallbackContext):
    """Обробляє текстові повідомлення залежно від стану розмови."""
    text = update.message.text
    if "editing_course_id" in context.user_data:
        course_id = context.user_data.pop("editing_course_id")
        new_name = text
        # update_course_name(course_id, new_name) — приклад виклику функції
        await update.message.reply_text(f"✅ Назву курсу ID {course_id} оновлено на: {new_name}")
        return

    if update.message.text == "/cancel":
        context.user_data.clear()
        await update.message.reply_text("❌ Дію скасовано.")
        return

    state = context.user_data.get("state")
    # ✅ Обробка редагування користувача
    if "edit_field" in context.user_data and "edit_user_tag" in context.user_data:
        field = context.user_data.get("edit_field")
        telegram_tag = context.user_data.get("edit_user_tag")
        new_value = update.message.text

        with SessionLocal() as db:
            user = db.query(User).filter_by(TelegramTag=telegram_tag).first()
            if not user:
                await update.message.reply_text(f"❌ Користувача @{telegram_tag} не знайдено.")
                context.user_data.clear()
                return

            try:
                if field == "name":
                    user.UserName = new_value
                    db.commit()
                elif field == "phone":
                    user.PhoneNumber = new_value
                    db.commit()
                elif field == "year":
                    student = db.query(Student).filter_by(UserID=user.UserID).first()
                    if student:
                        try:
                            year = int(new_value)
                            student.AdmissionYear = year
                            db.commit()
                        except ValueError:
                            await update.message.reply_text("❌ Рік вступу повинен бути числом.")
                            return
                    else:
                        await update.message.reply_text("❌ Цей користувач не є студентом.")
                        return
                elif field == "group":
                    student = db.query(Student).filter_by(UserID=user.UserID).first()
                    if student:
                        # Спочатку перевіряємо, чи існує група з таким ім'ям
                        group = db.query(StudentGroup).filter_by(GroupName=new_value).first()
                        if group:
                            student.GroupID = group.GroupID
                            db.commit()
                        else:
                            # Якщо введено ID групи замість назви
                            try:
                                group_id = int(new_value)
                                group = db.query(StudentGroup).filter_by(GroupID=group_id).first()
                                if group:
                                    student.GroupID = group_id
                                    db.commit()
                                else:
                                    await update.message.reply_text(f"❌ Групу з ID {group_id} не знайдено.")
                                    context.user_data.clear()
                                    return
                            except ValueError:
                                await update.message.reply_text("❌ Такої групи не існує.")
                                context.user_data.clear()
                                return
                    else:
                        await update.message.reply_text("❌ Цей користувач не є студентом.")
                        context.user_data.clear()
                        return

                await update.message.reply_text(f"✅ Дані користувача @{telegram_tag} успішно оновлено.")

                # Відправляємо повідомлення користувачу про зміну його даних
                if user.ChatID:
                    field_names = {
                        "name": "ім'я",
                        "phone": "номер телефону",
                        "group": "група",
                        "year": "рік вступу"
                    }
                    try:
                        await context.bot.send_message(
                            chat_id=user.ChatID,
                            text=f"ℹ️ Адміністратор змінив ваші дані: {field_names[field]} встановлено на '{new_value}'."
                        )
                    except Exception as e:
                        logging.error(f"Помилка відправки повідомлення користувачу: {e}")

            except SQLAlchemyError as e:
                logger.exception(f"Помилка при оновленні даних користувача: {e}")
                db.rollback()
                await update.message.reply_text("❌ Помилка бази даних при оновленні даних користувача.")

        # Скидаємо дані контексту
        if "edit_field" in context.user_data:
            del context.user_data["edit_field"]
        if "edit_user_tag" in context.user_data:
            del context.user_data["edit_user_tag"]

        return

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
        await confirm_command(update, context)
        return

    elif state == WAITING_FOR_STUDENT_DETAILS:
        data = update.message.text.split(",")
        if  len(data) != 5:
            await update.message.reply_text("❌ Неправильний формат! Введіть 5 параметрів через кому.")
            return
        context.user_data["new_user_name"] = data[0].strip()
        context.user_data["new_phone"] = data[1].strip()
        context.user_data["new_group"] = data[2].strip()
        context.user_data["new_admission_year"] = int(data[3].strip())
        context.user_data["new_specialty"] = data[4].strip()

        await save_new_user(update, context)
        await update.message.reply_text("✅ Заявка успішно подана! Очікуйте на повідомлення про підтвердження заявки на реєстрацію працівником деканату.")
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

    elif state == WAITING_FOR_SCAN_LINK:

        scan_link = update.message.text
        request_id = context.user_data.pop("processing_request_id")

        with SessionLocal() as db:
            request = db.query(DocumentRequest).filter(DocumentRequest.RequestID == request_id).first()
            request.Status = 'approved'
            db.commit()

            student = db.query(Student).filter(Student.StudentID == request.StudentID).first()
            user = db.query(User).filter(User.UserID == student.UserID).first()

            await context.bot.send_message(
                chat_id=user.ChatID,
                text=f"✅ Ваша заявка №{request.RequestID} опрацьована!\nВи маєте можливість отримати паперову версію у деканаті або скан-копію документу за посиланням: {scan_link}"
            )

        await update.message.reply_text(f"Заявку №{request_id} оновлено та студенту надіслано посилання.")


    # Обробка кнопок
    await handle_button_click(update, context)
