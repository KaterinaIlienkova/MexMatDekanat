from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
import datetime as dt

from source.auth.registration import check_registration

from source.database import SessionLocal
from source.db_queries import get_chat_ids_by_departments, get_chat_ids_by_admission_years, get_chat_ids_by_teachers, \
    get_chat_ids_by_groups
import datetime as dt
import logging
from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.fsm.context import FSMContext

from source.models import User, Student, Teacher, Department
from source.db_queries import (
    get_chat_ids_by_groups,
    get_chat_ids_by_admission_years,
    get_chat_ids_by_teachers,
    get_chat_ids_by_departments,
)
from source.auth.registration import check_registration
from source.states import Announcement

logger = logging.getLogger(__name__)
announcement_router = Router()

# Функція для ініціювання публікації оголошення
@announcement_router.message(F.text == "/announcement")
async def start_publication(message: Message, state: FSMContext):
    """Ініціює процес відправки оголошення."""
    # Перевіряємо, чи користувач має роль dean_office
    role = await check_registration(message)
    if role != "dean_office":
        await message.reply("У вас немає доступу до цієї функції.")
        return

    # Запитуємо, яким категоріям користувачів відправляти оголошення
    keyboard = [
        [InlineKeyboardButton(text="Студентам", callback_data="announce_to_students")],
        [InlineKeyboardButton(text="Викладачам", callback_data="announce_to_teachers")],
        [InlineKeyboardButton(text="Скасувати", callback_data="cancel_announcement")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    await message.reply(
        "Кому ви хочете надіслати оголошення?",
        reply_markup=reply_markup
    )

# Обробник для вибору отримувачів оголошення
@announcement_router.callback_query(F.data.startswith("announce_") | F.data == "cancel_announcement")
async def announcement_selector_handler(callback: CallbackQuery, state: FSMContext):
    """Обробляє вибір категорії отримувачів оголошення."""
    await callback.answer()

    if callback.data == "cancel_announcement":
        await callback.message.edit_text("Розсилку оголошення скасовано.")
        return

    elif callback.data == "announce_to_students":
        # Зберігаємо інформацію про категорію отримувачів
        await state.update_data(announcement_to="students")
        await show_student_course_selector(callback)

    elif callback.data == "announce_to_teachers":
        # Зберігаємо інформацію про категорію отримувачів
        await state.update_data(announcement_to="teachers")
        await show_department_selector(callback)

@announcement_router.callback_query(F.data.startswith("course_"))
async def course_selector_handler(callback: CallbackQuery, state: FSMContext):
    """Обробляє вибір курсу."""
    await callback.answer()

    course_year = int(callback.data.split("_")[1])
    data = await state.get_data()

    # Зберігаємо або додаємо вибраний курс до списку
    selected_courses = data.get("selected_courses", [])

    # Перевіряємо, чи курс уже вибраний
    if course_year in selected_courses:
        selected_courses.remove(course_year)
    else:
        selected_courses.append(course_year)

    await state.update_data(selected_courses=selected_courses)

    # Оновлюємо селектор курсів
    await update_course_selector(callback, state)

@announcement_router.callback_query(F.data.startswith("dept_"))
async def department_selector_handler(callback: CallbackQuery, state: FSMContext):
    """Обробляє вибір кафедри."""
    await callback.answer()

    dept_id = int(callback.data.split("_")[1])
    data = await state.get_data()

    # Зберігаємо або додаємо вибрану кафедру до списку
    selected_departments = data.get("selected_departments", [])

    # Перевіряємо, чи кафедра вже вибрана
    if dept_id in selected_departments:
        selected_departments.remove(dept_id)
    else:
        selected_departments.append(dept_id)

    await state.update_data(selected_departments=selected_departments)

    # Оновлюємо селектор кафедр
    await update_department_selector(callback, state)

@announcement_router.callback_query(F.data == "show_groups")
async def show_groups_handler(callback: CallbackQuery, state: FSMContext):
    """Показує групи для вибраних курсів."""
    await callback.answer()
    await show_group_selector(callback, state)

@announcement_router.callback_query(F.data.startswith("group_"))
async def group_selector_handler(callback: CallbackQuery, state: FSMContext):
    """Обробляє вибір групи."""
    await callback.answer()

    group_id = int(callback.data.split("_")[1])
    data = await state.get_data()

    # Зберігаємо або додаємо вибрану групу до списку
    selected_groups = data.get("selected_groups", [])

    # Перевіряємо, чи група вже вибрана
    if group_id in selected_groups:
        selected_groups.remove(group_id)
    else:
        selected_groups.append(group_id)

    await state.update_data(selected_groups=selected_groups)

    # Оновлюємо селектор груп
    await update_group_selector(callback, state)

@announcement_router.callback_query(F.data == "show_teachers")
async def show_teachers_handler(callback: CallbackQuery, state: FSMContext):
    """Показує викладачів для вибраних кафедр."""
    await callback.answer()
    await show_teacher_selector(callback, state)

@announcement_router.callback_query(F.data.startswith("teacher_"))
async def teacher_selector_handler(callback: CallbackQuery, state: FSMContext):
    """Обробляє вибір викладача."""
    await callback.answer()

    teacher_id = int(callback.data.split("_")[1])
    data = await state.get_data()

    # Зберігаємо або додаємо вибраного викладача до списку
    selected_teachers = data.get("selected_teachers", [])

    # Перевіряємо, чи викладач уже вибраний
    if teacher_id in selected_teachers:
        selected_teachers.remove(teacher_id)
    else:
        selected_teachers.append(teacher_id)

    await state.update_data(selected_teachers=selected_teachers)

    # Оновлюємо селектор викладачів
    await update_teacher_selector(callback, state)

@announcement_router.callback_query(F.data == "confirm_student_selection")
async def confirm_students_handler(callback: CallbackQuery, state: FSMContext):
    """Підтверджує вибір студентів і просить текст оголошення."""
    await callback.answer()
    await state.set_state(Announcement.waiting_for_text)
    await callback.message.edit_text(
        "Ви обрали отримувачів оголошення. Будь ласка, надішліть текст оголошення:"
    )

@announcement_router.callback_query(F.data == "confirm_teacher_selection")
async def confirm_teachers_handler(callback: CallbackQuery, state: FSMContext):
    """Підтверджує вибір викладачів і просить текст оголошення."""
    await callback.answer()
    await state.set_state(Announcement.waiting_for_text)
    await callback.message.edit_text(
        "Ви обрали отримувачів оголошення. Будь ласка, надішліть текст оголошення:"
    )

@announcement_router.callback_query(F.data == "back_to_courses")
async def back_to_courses_handler(callback: CallbackQuery):
    """Повертає до вибору курсів."""
    await callback.answer()
    await show_student_course_selector(callback)

@announcement_router.callback_query(F.data == "back_to_departments")
async def back_to_departments_handler(callback: CallbackQuery):
    """Повертає до вибору кафедр."""
    await callback.answer()
    await show_department_selector(callback)

@announcement_router.message(Announcement.waiting_for_text)
async def send_announcement(message: Message, state: FSMContext):
    """Відправляє оголошення вибраним користувачам з підтримкою різних типів медіа."""
    try:
        # Отримуємо дані стану
        data = await state.get_data()
        announcement_to = data.get("announcement_to")

        # Підготовка статистики для адміністратора
        recipients_count = 0
        chat_ids = []

        # Визначаємо текст оголошення
        announcement_text = message.text or message.caption or "Оголошення без тексту"

        with SessionLocal() as db:
            if announcement_to == "students":
                # Отримуємо chat_id для вибраних груп, якщо вони є
                selected_groups = data.get("selected_groups", [])
                if selected_groups:
                    chat_ids = get_chat_ids_by_groups(db, selected_groups)
                    group_stats = f"{len(selected_groups)} груп"
                else:
                    # Якщо групи не вибрані, але вибрані курси - відправляємо за курсами
                    selected_courses = data.get("selected_courses", [])
                    if selected_courses:
                        # Обчислюємо роки вступу для вибраних курсів
                        current_year = dt.datetime.now().year
                        admission_years = [current_year - course + 1 for course in selected_courses]

                        # Отримуємо chat_id для всіх студентів вказаних курсів (років вступу)
                        chat_ids = get_chat_ids_by_admission_years(db, admission_years)
                        group_stats = f"всі групи {len(selected_courses)} курсів"

            elif announcement_to == "teachers":
                # Отримуємо chat_id для вибраних викладачів, якщо вони є
                selected_teachers = data.get("selected_teachers", [])
                if selected_teachers:
                    chat_ids = get_chat_ids_by_teachers(db, selected_teachers)
                    teacher_stats = f"{len(selected_teachers)} викладачів"
                else:
                    # Якщо викладачі не вибрані, але вибрані кафедри
                    selected_departments = data.get("selected_departments", [])
                    if selected_departments:
                        # Отримуємо chat_id для всіх викладачів вказаних кафедр
                        chat_ids = get_chat_ids_by_departments(db, selected_departments)
                        teacher_stats = f"всі викладачі {len(selected_departments)} кафедр"

        # Відправляємо оголошення всім вибраним користувачам
        chat_ids = [chat_id[0] for chat_id in chat_ids]  # Розпакування ChatID
        bot = message.bot

        for chat_id in chat_ids:
            if chat_id:
                try:
                    # Надсилання різних типів медіа
                    if message.text:
                        # Текстове повідомлення
                        await bot.send_message(
                            chat_id=chat_id,
                            text=f"📢 ОГОЛОШЕННЯ:\n\n{message.text}"
                        )
                        recipients_count += 1

                    if message.photo:
                        # Беремо останню (найбільшу) версію фото
                        photo = message.photo[-1]

                        # Додаткова перевірка file_id
                        logger.info(f"Надсилаю фото з file_id: {photo.file_id}")

                        try:
                            await bot.send_photo(
                                chat_id=chat_id,
                                photo=photo.file_id,
                                caption=f"📢 ОГОЛОШЕННЯ:\n\n{message.caption or announcement_text}"
                            )
                            recipients_count += 1
                        except Exception as e:
                            logger.error(f"Помилка надсилання фото: {e}")

                    if message.video:
                        # Надсилання відео
                        await bot.send_video(
                            chat_id=chat_id,
                            video=message.video.file_id,
                            caption=f"📢 ОГОЛОШЕННЯ:\n\n{message.caption or announcement_text}"
                        )
                        recipients_count += 1

                    if message.document:
                        # Надсилання документа
                        await bot.send_document(
                            chat_id=chat_id,
                            document=message.document.file_id,
                            caption=f"📢 ОГОЛОШЕННЯ:\n\n{message.caption or announcement_text}"
                        )
                        recipients_count += 1

                except Exception as e:
                    logger.error(f"Помилка відправки повідомлення до chat_id {chat_id}: {e}")

        # Формуємо повідомлення з результатами розсилки
        if recipients_count > 0:
            summary_message = "✅ Оголошення успішно відправлено!\n\n"
            summary_message += f"Категорія: {'Студенти' if announcement_to == 'students' else 'Викладачі'}\n"

            if announcement_to == "students":
                selected_groups = data.get("selected_groups", [])
                selected_courses = data.get("selected_courses", [])

                if selected_groups:
                    summary_message += f"Охоплено {len(selected_groups)} груп\n"
                elif selected_courses:
                    summary_message += f"Охоплено студентів {len(selected_courses)} курсів\n"
            else:
                selected_teachers = data.get("selected_teachers", [])
                selected_departments = data.get("selected_departments", [])

                if selected_teachers:
                    summary_message += f"Охоплено {len(selected_teachers)} викладачів\n"
                elif selected_departments:
                    summary_message += f"Охоплено викладачів {len(selected_departments)} кафедр\n"

            summary_message += f"Успішно доставлено: {recipients_count} користувачам\n"
            summary_message += f"\nТекст оголошення:\n\n{announcement_text}"
            await message.reply(summary_message)
        else:
            await message.reply(
                "❌ Не вдалося надіслати оголошення. Можливі причини:\n"
                "- Немає отримувачів з Telegram ID в базі\n"
                "- Не вибрано жодного отримувача\n"
                "Переконайтеся, що ви правильно обрали отримувачів."
            )

    except Exception as e:
        logger.exception(f"Помилка при відправці оголошення: {e}")
        await message.reply(
            f"❌ Сталася помилка при відправці оголошення: {str(e)}\n"
            "Будь ласка, спробуйте пізніше або зверніться до адміністратора."
        )
    finally:
        # Очищаємо дані після відправки
        await state.clear()

# Допоміжні функції для створення і оновлення селекторів
async def show_student_course_selector(callback: CallbackQuery):
    """Показує селектор курсів для студентів."""
    # Визначаємо доступні курси (зазвичай 1-6)
    courses = range(1, 7)

    keyboard = []
    # Створюємо рядки кнопок для кожного курсу
    for course in courses:
        button = InlineKeyboardButton(
            text=f"{course} курс",
            callback_data=f"course_{course}"
        )
        keyboard.append([button])

    # Додаємо кнопку для переходу до вибору груп
    keyboard.append([
        InlineKeyboardButton(
            text="Далі: Вибір груп",
            callback_data="show_groups"
        )
    ])

    # Додаємо кнопку скасування
    keyboard.append([
        InlineKeyboardButton(
            text="Скасувати",
            callback_data="cancel_announcement"
        )
    ])

    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

    await callback.message.edit_text(
        "Виберіть курси, для яких відправлятиметься оголошення:",
        reply_markup=reply_markup
    )

async def update_course_selector(callback: CallbackQuery, state: FSMContext):
    """Оновлює селектор курсів з відміченими вибраними курсами."""
    data = await state.get_data()
    selected_courses = data.get("selected_courses", [])

    # Визначаємо доступні курси (зазвичай 1-6)
    courses = range(1, 7)

    keyboard = []
    # Створюємо рядки кнопок для кожного курсу з відміткою вибраних
    for course in courses:
        button_text = f"{course} курс ✅" if course in selected_courses else f"{course} курс"
        button = InlineKeyboardButton(
            text=button_text,
            callback_data=f"course_{course}"
        )
        keyboard.append([button])

    # Додаємо кнопку для переходу до вибору груп
    keyboard.append([
        InlineKeyboardButton(
            text="Далі: Вибір груп",
            callback_data="show_groups"
        )
    ])

    # Додаємо кнопку скасування
    keyboard.append([
        InlineKeyboardButton(
            text="Скасувати",
            callback_data="cancel_announcement"
        )
    ])

    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

    await callback.message.edit_text(
        "Виберіть курси, для яких відправлятиметься оголошення:",
        reply_markup=reply_markup
    )

async def show_department_selector(callback: CallbackQuery):
    """Показує селектор кафедр для викладачів."""
    # Отримуємо список кафедр з бази даних
    with SessionLocal() as db:
        departments = db.query(Department).all()

    keyboard = []
    # Створюємо рядки кнопок для кожної кафедри
    for dept in departments:
        button = InlineKeyboardButton(
            text=dept.Name,
            callback_data=f"dept_{dept.DepartmentID}"
        )
        keyboard.append([button])

    # Додаємо кнопку для переходу до вибору викладачів
    keyboard.append([
        InlineKeyboardButton(
            text="Далі: Вибір викладачів",
            callback_data="show_teachers"
        )
    ])

    # Додаємо кнопку скасування
    keyboard.append([
        InlineKeyboardButton(
            text="Скасувати",
            callback_data="cancel_announcement"
        )
    ])

    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

    await callback.message.edit_text(
        "Виберіть кафедри, для яких відправлятиметься оголошення:",
        reply_markup=reply_markup
    )

# Додаткові допоміжні функції будуть реалізовані відповідно до потреб
# show_group_selector, update_group_selector, show_teacher_selector, update_teacher_selector, etc.