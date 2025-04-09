from sqlalchemy.exc import SQLAlchemyError
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CallbackQueryHandler
from sqlalchemy.orm import Session

from source.config import WAITING_FOR_USER_ROLE, WAITING_FOR_USER_DETAILS, WAITING_FOR_STUDENT_DETAILS
from source.database import SessionLocal
from sqlalchemy import text
from typing import Any, Optional
from sqlalchemy.orm import Session
from source.models import User, Student, Teacher, StudentGroup, DeanOfficeStaff, Department, Specialty
import logging
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
                     KeyboardButton("Редагувати Q&A"), KeyboardButton("Оголошення"), KeyboardButton("Підтвердити реєстрацію")]]
    elif role == "student":
        keyboard = [[KeyboardButton("Q&A")],[KeyboardButton("Мої поточні курси")]]  # Q&A на панельці для студентів
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
    """Показує всіх неверифікованих студентів для підтвердження"""
    # Отримання всіх неверифікованих студентів
    with SessionLocal() as db:
        unconfirmed_users = db.query(User).filter_by(IsConfirmed=False, Role='student').all()

        if not unconfirmed_users:
            await update.message.reply_text("Немає неверифікованих студентів на даний момент.")
            return

        # Створюємо повідомлення зі списком усіх заявок
        message_text = "📋 Список заявок на підтвердження:\n\n"

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

        # Створюємо клавіатуру з номерами заявок
        keyboard = []
        row = []

        for i, user in enumerate(unconfirmed_users, 1):
            # Створюємо кнопки по 3 в ряд
            button = InlineKeyboardButton(f"#{i}", callback_data=f"confirm_{user.TelegramTag}")
            row.append(button)

            if len(row) == 3 or i == len(unconfirmed_users):
                keyboard.append(row)
                row = []

        # Додаємо кнопку скасування
        keyboard.append([InlineKeyboardButton("Скасувати", callback_data="cancel_confirmation")])

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            message_text + "Натисніть на номер заявки, щоб підтвердити реєстрацію:",
            reply_markup=reply_markup
        )
async def confirm_callback_handler(update: Update, context: CallbackContext) -> None:
    """Обробляє натискання кнопок підтвердження користувачів"""
    query = update.callback_query
    logging.info(f"confirm_callback_handler отримав запит: {query.data}")
    await query.answer()
    logging.info(f"Отримано callback-запит: {query.data}")

    if query.data == "cancel_confirmation":
        await query.edit_message_text("Операцію скасовано.")
        return

    # Отримуємо telegram_tag користувача
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