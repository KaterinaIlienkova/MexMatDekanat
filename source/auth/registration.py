import telegram
from sqlalchemy.exc import SQLAlchemyError
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CallbackQueryHandler, ConversationHandler, MessageHandler, CommandHandler, \
    filters
from sqlalchemy.orm import Session

from source.config import WAITING_FOR_USER_ROLE, WAITING_FOR_USER_DETAILS, WAITING_FOR_STUDENT_DETAILS, \
    WAITING_FOR_EDIT_FIELD
from source.database import SessionLocal
from sqlalchemy import text
from typing import Any, Optional
from sqlalchemy.orm import Session
from source.models import User, Student, Teacher, StudentGroup, DeanOfficeStaff, Department, Specialty, DocumentRequest, \
    CourseEnrollment, Course, PersonalQuestion
import logging
from telegram.error import BadRequest

logger = logging.getLogger(__name__)

from source.models import Student, StudentGroup, Department, Teacher, User

async def check_registration(update: Update, context: CallbackContext) -> Optional[str]:
    with SessionLocal() as db:
        user = update.message.from_user
        telegram_tag = user.username
        chat_id = update.effective_chat.id

        if telegram_tag:
            update_chat_id(db, telegram_tag, chat_id)
        else:
            await update.message.reply_text("❌ У вашому профілі Telegram відсутнє ім'я користувача. Будь ласка, встановіть його в налаштуваннях Telegram.")
            return None

        existing_user = db.query(User).filter_by(TelegramTag=telegram_tag).first()
        if not existing_user:
            context.user_data["state"] = WAITING_FOR_STUDENT_DETAILS
            context.user_data["new_telegram_tag"] = telegram_tag
            context.user_data["new_chat_id"] = chat_id
            context.user_data["new_role"] = "student"
            await update.message.reply_text(
                "🔒 Ви не зареєстровані.\n"
                "Будь ласка, надайте додаткові дані для завершення реєстрації.\n\n"
                "✏️ Введіть ваше ім'я, номер телефону, групу, рік вступу та спеціальність через кому.\n\n"
                "📌 Приклад:\n"
                "Іван Петренко, +380961234567, ФІ-21, 2023, Комп'ютерні науки"
            )
            return None
        elif not existing_user.IsConfirmed:
            await update.message.reply_text("⏳ Ваша заявка на реєстрацію ще не підтверджена працівником деканату.")
            return None
        return existing_user.Role



def get_user_role(session: Session, telegram_tag: str) -> str:
    """Отримує роль користувача за TelegramTag."""
    try:
        user = session.query(User).filter_by(TelegramTag=telegram_tag).first()
        return user.Role if user else "Невідомий"
    except SQLAlchemyError as e:
        logger.exception(f"Помилка при отриманні ролі користувача: {e}")
        return "Невідомий"

def update_chat_id(session: Session, telegram_tag: str, chat_id: int) -> bool:
    """Оновлює chat_id користувача."""
    try:
        user = session.query(User).filter_by(TelegramTag=telegram_tag).first()
        if user:
            user.ChatID = chat_id
            session.commit()
            return True
        return False
    except SQLAlchemyError as e:
        logger.exception(f"Помилка при оновленні chat_id користувача: {e}")
        session.rollback()
        return False



async def start(update: Update, context: CallbackContext):
    """Обробляє команду /start."""
    role = await check_registration(update, context)
    if role is None:
        return  # Виходимо, якщо користувач не зареєстрований

    if role == "dean_office":
        keyboard = [[KeyboardButton("Інструкції"), KeyboardButton("Додати користувача"),
                     KeyboardButton("Редагувати Q&A"), KeyboardButton("Оголошення"),
                     KeyboardButton("Підтвердити реєстрацію"), KeyboardButton("Заявки на документи")]]
    elif role == "student":
        keyboard = [[KeyboardButton("Q&A")],[KeyboardButton("Мої поточні курси")],[KeyboardButton("Замовити документ")]]  # Q&A на панельці для студентів
    elif role == "teacher":
        keyboard = [[KeyboardButton("Списки студентів")]]
    else:
        keyboard = []

    if keyboard:
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
        await update.message.reply_text(
            f"Вітаю, {update.message.from_user.username}! Ви зареєстровані як {role}.",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            f"Вітаю, {update.message.from_user.username}! Ви зареєстровані як {role}."
        )


def add_user(session: Session, username: str, telegram_tag: str, role: str, phone_number: str, chat_id: Optional[int] = None, group_name: Optional[str] = None, admission_year: Optional[int] = None, email: Optional[str] = None, department_id: Optional[int] = None, position: Optional[str] = None) -> Optional[User]:
    """
    Додає нового користувача і відповідний запис у відповідну таблицю на основі ролі.
    """
    existing_user = session.query(User).filter_by(TelegramTag=telegram_tag).first()
    if existing_user:
        return None  # Користувач вже існує

    # Створюємо нового користувача
    user = User(
        UserName=username,
        TelegramTag=telegram_tag,
        Role=role,
        PhoneNumber=phone_number,
        ChatID=chat_id,
        IsConfirmed=False  # Нові користувачі подають заявку
    )

    session.add(user)
    session.flush()  # Отримуємо UserID не комітячи

    # Додаємо дані в залежності від ролі
    if role == "student" and group_name and admission_year:
        student_group = session.query(StudentGroup).filter_by(GroupName=group_name).first()
        if not student_group:
            session.rollback()
            raise ValueError(f"Група '{group_name}' не знайдена")

        student = Student(
            UserID=user.UserID,
            GroupID=student_group.GroupID,
            AdmissionYear=admission_year
        )
        session.add(student)

    elif role == "teacher" and email and department_id:
        teacher = Teacher(
            UserID=user.UserID,
            Email=email,
            DepartmentID=department_id
        )
        session.add(teacher)

    elif role == "dean_office" and position:
        staff = DeanOfficeStaff(
            UserID=user.UserID,
            Position=position
        )
        session.add(staff)

    session.commit()
    return user



def add_student(session: Session, user_id: int, group_name: str, admission_year: int, specialty_name: Optional[str] = None) -> bool:
    """
    Додає запис студента для існуючого користувача.
    Якщо вказана спеціальність і група не існує, створює нову групу з цією спеціальністю.
    """
    try:
        # Перевіряємо чи існує користувач
        user = session.query(User).filter_by(UserID=user_id).first()
        if not user:
            return False

        # Шукаємо групу
        student_group = session.query(StudentGroup).filter_by(GroupName=group_name).first()

        # Якщо групи немає і вказана спеціальність, створюємо нову групу
        if not student_group and specialty_name:
            # Шукаємо спеціальність
            specialty = session.query(Specialty).filter_by(Name=specialty_name).first()
            if not specialty:
                # Створюємо нову спеціальність, якщо не існує
                specialty = Specialty(Name=specialty_name)
                session.add(specialty)
                session.flush()

            # Створюємо нову групу
            student_group = StudentGroup(
                GroupName=group_name,
                SpecialtyID=specialty.SpecialtyID
            )
            session.add(student_group)
            session.flush()
        elif not student_group:
            return False  # Група не існує і не можемо створити нову без спеціальності

        # Створюємо запис студента
        new_student = Student(
            UserID=user_id,
            GroupID=student_group.GroupID,
            AdmissionYear=admission_year
        )

        session.add(new_student)
        session.commit()
        return True
    except Exception as e:
        logger.exception("Помилка при додаванні студента: %s", e)
        session.rollback()
        return False


def add_teacher(session: Session, user_id: int, email: str, department_id: int) -> bool:
    """
    Додає запис викладача для існуючого користувача.
    """
    try:
        # Перевіряємо чи існує користувач
        user = session.query(User).filter_by(UserID=user_id).first()
        if not user:
            return False

        # Перевіряємо чи існує департамент
        department = session.query(Department).filter_by(DepartmentID=department_id).first()
        if not department:
            return False

        # Створюємо запис викладача
        new_teacher = Teacher(
            UserID=user_id,
            Email=email,
            DepartmentID=department_id
        )

        session.add(new_teacher)
        session.commit()
        return True
    except Exception as e:
        logger.exception("Помилка при додаванні викладача: %s", e)
        session.rollback()
        return False


async def save_new_user(update: Update, context: CallbackContext):
    """Зберігає нового користувача в БД через ORM."""
    with SessionLocal() as db:
        user = add_user(db, context.user_data["new_user_name"], context.user_data["new_telegram_tag"],
                        context.user_data["new_role"], context.user_data["new_phone"],context.user_data["new_chat_id"])
        if user is None:
            await update.message.reply_text("❌ Користувач із таким TelegramTag вже існує.")
            return

        role = context.user_data["new_role"]
        success = False

        if role == "student":
            success = add_student(db, user.UserID, context.user_data["new_group"],
                                  context.user_data["new_admission_year"], context.user_data["new_specialty"])
        elif role == "teacher":
            success = add_teacher(db, user.UserID, context.user_data["new_email"], context.user_data["new_department"])

        if success:
            await update.message.reply_text(f"✅ Дані збережено!")
        else:
            await update.message.reply_text(f"❌ Помилка при додаванні {role}.")

    context.user_data.clear()

async def prompt_user_details(update: Update, context: CallbackContext):
    context.user_data["state"] = WAITING_FOR_USER_ROLE  # Перевірте, що цей рядок є у функції
    await update.message.reply_text("Виберіть роль нового користувача: student або teacher")
def confirm_user(session: Session, telegram_tag: str) -> bool:
    user = session.query(User).filter_by(TelegramTag=telegram_tag).first()
    if user and not user.IsConfirmed:
        user.IsConfirmed = True
        session.commit()
        return True
    return False

def delete_user(session: Session, telegram_tag: str) -> bool:
    """Видаляє заявку користувача на реєстрацію."""
    try:
        user = session.query(User).filter_by(TelegramTag=telegram_tag).first()

        if not user:
            return False  # Користувача не знайдено

        # Видаляємо залежні записи, якщо вони є
        if user.Role == "student":
            session.query(DocumentRequest).filter_by(StudentID=user.students.StudentID).delete()
            session.query(CourseEnrollment).filter_by(StudentID=user.students.StudentID).delete()
            session.delete(user.students)

        elif user.Role == "teacher":
            session.query(Course).filter_by(TeacherID=user.teachers.TeacherID).delete()
            session.delete(user.teachers)

        elif user.Role == "dean_office":
            session.delete(user.dean_office_staff)

        # Видаляємо особисті питання
        session.query(PersonalQuestion).filter_by(UserID=user.UserID).delete()

        # Видаляємо самого користувача
        session.delete(user)
        session.commit()

        return True

    except SQLAlchemyError as e:
        logger.exception(f"Помилка при видаленні заявки користувача: {e}")
        session.rollback()
        return False


async def delete_user_handler(update: Update, context: CallbackContext):
    """Обробляє видалення заявки користувача."""
    query = update.callback_query
    await query.answer()

    callback_data = query.data

    if callback_data == "cancel_delete":
        await query.edit_message_text("❌ Видалення скасовано.")
        return

    # Отримуємо TelegramTag із callback_data
    try:
        telegram_tag = callback_data.replace("delete_", "")

        # Використовуємо SessionLocal як менеджер контексту
        with SessionLocal() as db:
            success = delete_user(db, telegram_tag)

            if success:
                await query.edit_message_text("✅ Заявку користувача успішно видалено.")
            else:
                await query.edit_message_text("❌ Не вдалося видалити заявку. Спробуйте пізніше.")
    except Exception as e:
        logger.exception(f"Помилка при видаленні заявки користувача: {e}")
        await query.edit_message_text("🚨 Сталася помилка при видаленні заявки.")


async def confirm_delete_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    telegram_tag = query.data.replace("confirm_delete_", "")

    with SessionLocal() as db:
        user = db.query(User).filter_by(TelegramTag=telegram_tag).first()
        if user:
            db.delete(user)
            db.commit()
            await query.edit_message_text(f"✅ Користувача @{telegram_tag} успішно видалено.")
        else:
            await query.edit_message_text(f"❌ Не вдалося знайти @{telegram_tag} для видалення.")


def update_user(session: Session, telegram_tag: str, new_data: dict) -> bool:
    user = session.query(User).filter_by(TelegramTag=telegram_tag).first()
    if user:
        for key, value in new_data.items():
            if hasattr(user, key):
                setattr(user, key, value)
        session.commit()
        return True
    return False



async def confirm_command(update: Update, context: CallbackContext):
    if not context.args:
        await update.message.reply_text("Використання: /confirm telegram_tag")
        return
    telegram_tag = context.args[0]
    with SessionLocal() as db:
        if confirm_user(db, telegram_tag):
            await update.message.reply_text(f"✅ Користувача @{telegram_tag} підтверджено.")
        else:
            await update.message.reply_text(f"❌ Не вдалося підтвердити @{telegram_tag}.")


async def confirm(update: Update, context: CallbackContext) -> None:
    """Показує всіх неверифікованих студентів для підтвердження, редагування або видалення"""

    # Отримання всіх неверифікованих студентів
    with SessionLocal() as db:
        unconfirmed_users = db.query(User).filter_by(IsConfirmed=False, Role='student').all()

        if not unconfirmed_users:
            await update.message.reply_text("Немає неверифікованих студентів на даний момент.")
            return

        # Створюємо повідомлення зі списком усіх заявок
        message_text = "📋 Список заявок на підтвердження:\n\n"

        keyboard = []
        row = []

        for i, user in enumerate(unconfirmed_users, 1):
            # Додаємо базову інформацію про користувача
            message_text += f"#{i} - {user.UserName} (@{user.TelegramTag})\n"
            message_text += f"📱 Телефон: {user.PhoneNumber or 'Не вказано'}\n"

            # Додаємо інформацію про студента
            student = db.query(Student).filter_by(UserID=user.UserID).first()
            if student:
                group = db.query(StudentGroup).filter_by(GroupID=student.GroupID).first()
                group_name = group.GroupName if group else "Невідома"
                message_text += f"👨‍🎓 Група: {group_name}\n"
                message_text += f"📅 Рік вступу: {student.AdmissionYear}\n"

            message_text += "\n"

            # Створюємо кнопки для підтвердження, редагування та видалення
            button = InlineKeyboardButton(f"✅ #{i}", callback_data=f"confirm_{user.TelegramTag}")
            edit_button = InlineKeyboardButton("✏️ Редагувати", callback_data=f"edit_{user.TelegramTag}")
            delete_button = InlineKeyboardButton("🗑 Видалити", callback_data=f"delete_{user.TelegramTag}")

            row.append(button)
            row.append(edit_button)
            row.append(delete_button)

            if len(row) == 3 or i == len(unconfirmed_users):
                keyboard.append(row)
                row = []

        # Додаємо кнопку скасування
        keyboard.append([InlineKeyboardButton("🚫 Скасувати", callback_data="cancel_confirmation")])

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            message_text + "Натисніть на номер заявки, щоб підтвердити реєстрацію, або використовуйте кнопки для редагування чи видалення:",
            reply_markup=reply_markup
        )


# async def confirm_callback_handler(update: Update, context: CallbackContext) -> None:
#     """Обробляє натискання кнопок підтвердження користувачів"""
#     query = update.callback_query
#     logging.info(f"confirm_callback_handler отримав запит: {query.data}")
#     await query.answer()
#     logging.info(f"Отримано callback-запит: {query.data}")
#
#     if query.data == "cancel_confirmation":
#         await query.edit_message_text("Операцію скасовано.")
#         return
#
#
#     if query.data.startswith("edit_"):
#         telegram_tag = query.data.replace("edit_", "")
#         await query.message.reply_text(f"✏️ Введіть нові дані для @{telegram_tag} у форматі: 'Поле=значення, Поле=значення'")
#         context.user_data["edit_user"] = telegram_tag
#         return
#
#     if query.data.startswith("delete_"):
#         telegram_tag = query.data.replace("delete_", "")
#         with SessionLocal() as db:
#             if delete_user(db, telegram_tag):
#                 await query.edit_message_text(f"🗑 Користувача @{telegram_tag} видалено.")
#             else:
#                 await query.edit_message_text(f"❌ Не вдалося видалити @{telegram_tag}.")
#         return
#     else:
#         # Отримуємо telegram_tag користувача
#         telegram_tag = query.data.replace("confirm_", "")
#
#         # Підтверджуємо користувача
#         with SessionLocal() as db:
#             if confirm_user(db, telegram_tag):
#                 # Отримуємо ім'я користувача для повідомлення
#                 user = db.query(User).filter_by(TelegramTag=telegram_tag).first()
#                 username = user.UserName if user else telegram_tag
#
#                 await query.edit_message_text(f"✅ Користувача {username} (@{telegram_tag}) успішно підтверджено.")
#
#                 # Надсилаємо повідомлення користувачу про підтвердження реєстрації
#                 if user and user.ChatID:
#                     try:
#                         await context.bot.send_message(
#                             chat_id=user.ChatID,
#                             text="✅ Вашу реєстрацію було підтверджено адміністратором. Тепер ви можете користуватися всіма функціями системи."
#                         )
#                     except Exception as e:
#                         logging.error(f"Помилка відправки повідомлення користувачу: {e}")
#             else:
#                 await query.edit_message_text(f"❌ Не вдалося підтвердити користувача @{telegram_tag}.")

async def edit_user_handler(update: Update, context: CallbackContext):
    """Обробляє редагування даних користувача"""
    query = update.callback_query
    await query.answer()

    # Отримання TelegramTag користувача, якого треба редагувати
    telegram_tag = query.data.replace("edit_", "")

    # Створюємо кнопки для вибору поля для редагування
    keyboard = [
        [
            InlineKeyboardButton("Ім'я", callback_data=f"edit_name_{telegram_tag}"),
            InlineKeyboardButton("Телефон", callback_data=f"edit_phone_{telegram_tag}")
        ],
        [
            InlineKeyboardButton("Група", callback_data=f"edit_group_{telegram_tag}"),
            InlineKeyboardButton("Рік вступу", callback_data=f"edit_year_{telegram_tag}")
        ],
        [InlineKeyboardButton("🚫 Скасувати", callback_data="cancel_edit")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"Виберіть, яке поле ви хочете змінити для користувача @{telegram_tag}:",
        reply_markup=reply_markup
    )

async def edit_field_handler(update: Update, context: CallbackContext):
    """Обробляє вибір поля для редагування"""
    query = update.callback_query
    await query.answer()

    if query.data == "cancel_edit":
        await query.edit_message_text("❌ Редагування скасовано.")
        return

    # Розбираємо callback_data для отримання поля та telegram_tag
    parts = query.data.split("_")
    field = parts[1]  # name, phone, group, year
    telegram_tag = parts[2]

    # Зберігаємо дані в контексті для використання в наступному хендлері
    context.user_data["edit_field"] = field
    context.user_data["edit_user_tag"] = telegram_tag

    field_names = {
        "name": "ім'я",
        "phone": "номер телефону",
        "group": "групу",
        "year": "рік вступу"
    }

    # Важливо: не редагуйте оригінальне повідомлення, а надішліть нове
    await query.edit_message_text(f"Очікую нове значення для {field_names[field]}...")
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=f"✏️ Введіть нове значення для поля '{field_names[field]}' користувача @{telegram_tag}:"
    )

async def process_edit_value(update: Update, context: CallbackContext):
    """Обробляє введене нове значення та оновлює базу даних"""
    new_value = update.message.text
    field = context.user_data.get("edit_field")
    telegram_tag = context.user_data.get("edit_user_tag")

    if not field or not telegram_tag:
        await update.message.reply_text("❌ Помилка: дані для редагування не знайдено.")
        return ConversationHandler.END

    with SessionLocal() as db:
        user = db.query(User).filter_by(TelegramTag=telegram_tag).first()
        if not user:
            await update.message.reply_text(f"❌ Користувача @{telegram_tag} не знайдено.")
            return ConversationHandler.END

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
                        return ConversationHandler.END
                else:
                    await update.message.reply_text("❌ Цей користувач не є студентом.")
                    return ConversationHandler.END
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
                                return ConversationHandler.END
                        except ValueError:
                            await update.message.reply_text("❌ Такої групи не існує.")
                            return ConversationHandler.END
                else:
                    await update.message.reply_text("❌ Цей користувач не є студентом.")
                    return ConversationHandler.END

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

    return ConversationHandler.END

# Функція для отримання списку груп для зручності вибору
async def get_groups_list(update: Update, context: CallbackContext):
    """Показує список доступних груп"""
    with SessionLocal() as db:
        groups = db.query(StudentGroup).all()

        if not groups:
            await update.message.reply_text("❌ У базі даних немає жодної групи.")
            return

        message_text = "📋 Доступні групи:\n\n"
        for group in groups:
            message_text += f"ID: {group.GroupID} - {group.GroupName}\n"

        await update.message.reply_text(message_text)

# Оновлення основного хендлера для обробки callback-запитів
async def confirm_callback_handler(update: Update, context: CallbackContext) -> None:
    """Обробляє натискання кнопок підтвердження та редагування користувачів"""
    query = update.callback_query
    logging.info(f"confirm_callback_handler отримав запит: {query.data}")
    await query.answer()

    # Обробка різних callback_data
    if query.data == "cancel_confirmation":
        await query.edit_message_text("Операцію скасовано.")
        return
    elif query.data == "cancel_edit":
        await query.edit_message_text("❌ Редагування скасовано.")
        return
    elif query.data.startswith("edit_"):
        if len(query.data.split("_")) == 2:  # Формат: edit_username
            await edit_user_handler(update, context)
            return
        elif len(query.data.split("_")) == 3:  # Формат: edit_field_username
            await edit_field_handler(update, context)
            return
    elif query.data.startswith("delete_"):
        telegram_tag = query.data.replace("delete_", "")
        with SessionLocal() as db:
            if delete_user(db, telegram_tag):
                await query.edit_message_text(f"🗑 Користувача @{telegram_tag} видалено.")
            else:
                await query.edit_message_text(f"❌ Не вдалося видалити @{telegram_tag}.")
        return
    elif query.data.startswith("confirm_"):
        # Отримуємо telegram_tag користувача для підтвердження
        telegram_tag = query.data.replace("confirm_", "")

        # Підтверджуємо користувача
        with SessionLocal() as db:
            if confirm_user(db, telegram_tag):
                # Отримуємо ім'я користувача для повідомлення
                user = db.query(User).filter_by(TelegramTag=telegram_tag).first()
                username = user.UserName if user else telegram_tag

                await query.edit_message_text(f"✅ Користувача {username} (@{telegram_tag}) успішно підтверджено.")

                # Надсилаємо повідомлення користувачу про підтвердження реєстрації
                if user and user.ChatID:
                    try:
                        await context.bot.send_message(
                            chat_id=user.ChatID,
                            text="✅ Вашу реєстрацію було підтверджено адміністратором. Тепер ви можете користуватися всіма функціями системи."
                        )
                    except Exception as e:
                        logging.error(f"Помилка відправки повідомлення користувачу: {e}")
            else:
                await query.edit_message_text(f"❌ Не вдалося підтвердити користувача @{telegram_tag}.")
# Додавання ConversationHandler для процесу редагування
edit_conv_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(edit_field_handler, pattern=r"^edit_[a-z]+_\w+$")
    ],
    states={
        "AWAITING_EDIT_VALUE": [MessageHandler(filters.TEXT & ~filters.COMMAND, process_edit_value)]
    },
    fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)]
)

# Функція для додавання хендлерів до диспетчера
def register_edit_handlers(application):
    """Реєструє обробники для функціоналу редагування"""
    application.add_handler(edit_conv_handler)
    application.add_handler(CommandHandler("groups", get_groups_list))
