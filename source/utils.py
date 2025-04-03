from telegram import Update
from telegram.ext import CallbackContext

from source.announcements.publication import send_announcement, start_publication
from source.auth.permissions import handle_button_click
from source.auth.registration import save_new_user

from source.database import SessionLocal
from source.faq.handlers import add_faq, update_faq, send_qa, show_edit_qa_options

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.exc import IntegrityError
from database import SessionLocal
from models import User, Student, Teacher
from source.states import UserRegistration, FAQ, Announcement


router = Router()

@router.message(F.text == "/cancel")
async def cancel_handler(message: Message, state: FSMContext):
    """Handles the cancel command to reset user state."""
    await state.clear()
    await message.reply("❌ Дію скасовано.")

@router.message(UserRegistration.waiting_for_role)
async def process_role(message: Message, state: FSMContext):
    """Process user role selection."""
    role = message.text.lower()
    if role not in ["student", "teacher"]:
        await message.reply("❌ Некоректна роль! Виберіть 'student' або 'teacher'.")
        return

    await state.update_data(new_role=role)
    await state.set_state(UserRegistration.waiting_for_details)

    if role == "student":
        await message.reply("✏️ Введіть ім'я користувача, TelegramTag, номер телефону, групу, рік вступу та спеціальність через кому.\n\n📌 Приклад: Іван Петренко, ivan_petrenko, +380961234567, ФІ-21, 2023, Комп'ютерні науки")
    else:  # Викладач
        await message.reply("✏️ Введіть ім'я користувача, TelegramTag, номер телефону, email та кафедру через кому.\n\n📌 Приклад: Петро Іванов, petro_ivanov, +380501234567, petro@example.com, Кафедра математики")

@router.message(UserRegistration.waiting_for_details)
async def process_user_details(message: Message, state: FSMContext):
    """Process user details input."""
    data = message.text.split(",")
    user_data = await state.get_data()
    role = user_data["new_role"]

    if role == "student" and len(data) != 6:
        await message.reply("❌ Неправильний формат! Введіть 6 параметрів через кому.")
        return
    if role == "teacher" and len(data) != 5:
        await message.reply("❌ Неправильний формат! Введіть 5 параметрів через кому.")
        return

    await state.update_data(
        new_user_name=data[0].strip(),
        new_telegram_tag=data[1].strip(),
        new_phone=data[2].strip()
    )

    if role == "student":
        await state.update_data(
            new_group=data[3].strip(),
            new_admission_year=int(data[4].strip()),
            new_specialty=data[5].strip()
        )
    else:  # Викладач
        await state.update_data(
            new_email=data[3].strip(),
            new_department=data[4].strip()
        )

    await save_new_user(message, state)

@router.message(FAQ.waiting_for_question)
async def process_question(message: Message, state: FSMContext):
    """Process new FAQ question."""
    await state.update_data(new_question=message.text)
    await state.set_state(FAQ.waiting_for_answer)
    await message.reply("✏️ Тепер введіть відповідь:")

@router.message(FAQ.waiting_for_answer)
async def process_answer(message: Message, state: FSMContext):
    """Process new FAQ answer."""
    data = await state.get_data()
    question = data.get("new_question", "")
    answer = message.text

    with SessionLocal() as db:
        success = add_faq(db, question, answer)

    if success:
        await message.reply("✅ Питання додано до FAQ!")
    else:
        await message.reply("❌ Помилка при додаванні питання.")

    await state.clear()

@router.message(FAQ.waiting_for_edit_answer)
async def process_edit_answer(message: Message, state: FSMContext):
    """Process FAQ answer editing."""
    data = await state.get_data()
    faq_id = data.get("edit_faq_id")
    new_answer = message.text

    with SessionLocal() as db:
        success = update_faq(db, faq_id, new_answer)

    if success:
        await message.reply("✅ Відповідь оновлено!")
    else:
        await message.reply("❌ Помилка при оновленні.")

    await state.clear()

@router.message(Announcement.waiting_for_text)
async def process_announcement_text(message: Message, state: FSMContext):
    """Process announcement text."""
    await send_announcement(message, state)

# Helper function to save a new user
async def save_new_user(message: Message, state: FSMContext):
    """Зберігає нового користувача в базі даних."""
    # Отримуємо дані зі стану
    user_data = await state.get_data()

    with SessionLocal() as db:
        try:
            # Створюємо користувача
            user = User(
                UserName=user_data["new_user_name"],
                TelegramTag=user_data["new_telegram_tag"],
                Role=user_data["new_role"],
                PhoneNumber=user_data["new_phone"]
            )
            db.add(user)
            db.commit()
            db.refresh(user)

            # Додаємо специфічні дані в залежності від ролі
            if user.Role == "student":
                student = Student(
                    UserID=user.UserID,
                    GroupID=user_data["new_group"],
                    AdmissionYear=user_data["new_admission_year"]
                )
                db.add(student)

            elif user.Role == "teacher":
                teacher = Teacher(
                    UserID=user.UserID,
                    DepartmentID=user_data["new_department"]
                )
                db.add(teacher)

            db.commit()

            await message.reply(f"✅ Користувач {user.UserName} ({user.TelegramTag}) успішно доданий як {user.Role}!")

        except IntegrityError:
            db.rollback()
            await message.reply("❌ Помилка: Користувач з таким TelegramTag вже існує!")
        except Exception as e:
            db.rollback()
            await message.reply(f"❌ Виникла помилка: {str(e)}")

    # Очищення стану
    await state.clear()

# Other handlers
@router.message(F.text == "Інструкції")
async def instructions_handler(message: Message):
    """Надсилає інструкції користувачеві."""
    await message.reply("Список команд:\n/start - Початок роботи\n/register - Реєстрація користувача\n/help - Допомога")

@router.message(F.text == "Додати користувача")
async def add_user_handler(message: Message, state: FSMContext):
    from source.auth.registration import prompt_user_details
    await prompt_user_details(message, state)

@router.message(F.text == "Q&A")
async def qa_handler(message: Message):
    await send_qa(message)

@router.message(F.text == "Редагувати Q&A")
async def edit_qa_handler(message: Message):
    await show_edit_qa_options(message)

@router.message(F.text == "Оголошення")
async def announcement_handler(message: Message, state: FSMContext):
    await start_publication(message, state)