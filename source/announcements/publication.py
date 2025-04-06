from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
import datetime as dt
from source.announcements.selectors import show_student_course_selector, show_department_selector, \
    update_course_selector, update_department_selector, show_group_selector, update_group_selector, \
    show_teacher_selector, update_teacher_selector
from source.auth.registration import check_registration

from source.config import (
    WAITING_FOR_QUESTION, WAITING_FOR_ANSWER,
    WAITING_FOR_EDIT_ANSWER, WAITING_FOR_ANNOUNCEMENT_TEXT,
    logger
)
from source.database import SessionLocal
from source.db_queries import get_chat_ids_by_departments, get_chat_ids_by_admission_years, get_chat_ids_by_teachers, \
    get_chat_ids_by_groups


# Основний обробник для вибору отримувачів оголошення
async def announcement_selector_handler(update: Update, context: CallbackContext):
    """Обробляє вибір категорії отримувачів оголошення."""
    query = update.callback_query
    await query.answer()

    if query.data == "cancel_announcement":
        await query.edit_message_text("Розсилку оголошення скасовано.")
        return

    elif query.data == "announce_to_students":
        # Зберігаємо інформацію про категорію отримувачів
        context.user_data["announcement_to"] = "students"
        await show_student_course_selector(update, context)

    elif query.data == "announce_to_teachers":
        # Зберігаємо інформацію про категорію отримувачів
        context.user_data["announcement_to"] = "teachers"
        await show_department_selector(update, context)

    elif query.data.startswith("course_"):
        # Обробляємо вибір курсу
        course_year = int(query.data.split("_")[1])

        # Зберігаємо або додаємо вибраний курс до списку
        if "selected_courses" not in context.user_data:
            context.user_data["selected_courses"] = []

        # Перевіряємо, чи курс уже вибраний
        if course_year in context.user_data["selected_courses"]:
            context.user_data["selected_courses"].remove(course_year)
        else:
            context.user_data["selected_courses"].append(course_year)

        # Оновлюємо селектор курсів
        await update_course_selector(update, context)

    elif query.data.startswith("dept_"):
        # Обробляємо вибір кафедри
        dept_id = int(query.data.split("_")[1])

        # Зберігаємо або додаємо вибрану кафедру до списку
        if "selected_departments" not in context.user_data:
            context.user_data["selected_departments"] = []

        # Перевіряємо, чи кафедра вже вибрана
        if dept_id in context.user_data["selected_departments"]:
            context.user_data["selected_departments"].remove(dept_id)
        else:
            context.user_data["selected_departments"].append(dept_id)

        # Оновлюємо селектор кафедр
        await update_department_selector(update, context)

    elif query.data == "show_groups":
        # Показуємо групи для вибраних курсів
        await show_group_selector(update, context)

    elif query.data.startswith("group_"):
        # Обробляємо вибір групи
        group_id = int(query.data.split("_")[1])

        # Зберігаємо або додаємо вибрану групу до списку
        if "selected_groups" not in context.user_data:
            context.user_data["selected_groups"] = []

        # Перевіряємо, чи група вже вибрана
        if group_id in context.user_data["selected_groups"]:
            context.user_data["selected_groups"].remove(group_id)
        else:
            context.user_data["selected_groups"].append(group_id)

        # Оновлюємо селектор груп
        await update_group_selector(update, context)

    elif query.data == "show_teachers":
        # Показуємо викладачів для вибраних кафедр
        await show_teacher_selector(update, context)

    elif query.data.startswith("teacher_"):
        # Обробляємо вибір викладача
        teacher_id = int(query.data.split("_")[1])

        # Зберігаємо або додаємо вибраного викладача до списку
        if "selected_teachers" not in context.user_data:
            context.user_data["selected_teachers"] = []

        # Перевіряємо, чи викладач уже вибраний
        if teacher_id in context.user_data["selected_teachers"]:
            context.user_data["selected_teachers"].remove(teacher_id)
        else:
            context.user_data["selected_teachers"].append(teacher_id)

        # Оновлюємо селектор викладачів
        await update_teacher_selector(update, context)

    elif query.data == "confirm_student_selection":
        # Підтверджуємо вибір студентів і просимо надіслати текст оголошення
        context.user_data["state"] = WAITING_FOR_ANNOUNCEMENT_TEXT
        await query.edit_message_text(
            "Ви обрали отримувачів оголошення. Будь ласка, надішліть текст оголошення:"
        )

    elif query.data == "confirm_teacher_selection":
        # Підтверджуємо вибір викладачів і просимо надіслати текст оголошення
        context.user_data["state"] = WAITING_FOR_ANNOUNCEMENT_TEXT
        await query.edit_message_text(
            "Ви обрали отримувачів оголошення. Будь ласка, надішліть текст оголошення:"
        )

    elif query.data == "back_to_courses":
        # Повертаємось до вибору курсів
        await show_student_course_selector(update, context)

    elif query.data == "back_to_departments":
        # Повертаємось до вибору кафедр
        await show_department_selector(update, context)

# Функція для ініціювання публікації оголошення
async def sent_publication(update: Update, context: CallbackContext):
    """Ініціює процес відправки оголошення."""
    # Перевіряємо, чи користувач має роль dean_office
    role = await check_registration(update, context)
    if role != "dean_office":
        await update.message.reply_text("У вас немає доступу до цієї функції.")
        return

    # Запитуємо, яким категоріям користувачів відправляти оголошення
    keyboard = [
        [InlineKeyboardButton("Студентам", callback_data="announce_to_students")],
        [InlineKeyboardButton("Викладачам", callback_data="announce_to_teachers")],
        [InlineKeyboardButton("Скасувати", callback_data="cancel_announcement")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Кому ви хочете надіслати оголошення?",
        reply_markup=reply_markup
    )

async def send_announcement(update: Update, context: CallbackContext):
    """Відправляє оголошення вибраним користувачам з підтримкою різних типів медіа."""
    try:
        # Отримуємо категорію отримувачів
        announcement_to = context.user_data.get("announcement_to")

        # Підготовка статистики для адміністратора
        recipients_count = 0
        chat_ids = []

        # Визначаємо текст оголошення
        announcement_text = update.message.text or update.message.caption or "Оголошення без тексту"

        with SessionLocal() as db:
            if announcement_to == "students":
                # Отримуємо chat_id для вибраних груп, якщо вони є
                selected_groups = context.user_data.get("selected_groups", [])
                if selected_groups:
                    chat_ids = get_chat_ids_by_groups(db, selected_groups)
                    group_stats = f"{len(selected_groups)} груп"
                else:
                    # Якщо групи не вибрані, але вибрані курси - відправляємо за курсами
                    selected_courses = context.user_data.get("selected_courses", [])
                    if selected_courses:
                        # Обчислюємо роки вступу для вибраних курсів
                        current_year = dt.datetime.now().year
                        admission_years = [current_year - course + 1 for course in selected_courses]

                        # Отримуємо chat_id для всіх студентів вказаних курсів (років вступу)
                        chat_ids = get_chat_ids_by_admission_years(db, admission_years)
                        group_stats = f"всі групи {len(selected_courses)} курсів"

            elif announcement_to == "teachers":
                # Отримуємо chat_id для вибраних викладачів, якщо вони є
                selected_teachers = context.user_data.get("selected_teachers", [])
                if selected_teachers:
                    chat_ids = get_chat_ids_by_teachers(db, selected_teachers)
                    teacher_stats = f"{len(selected_teachers)} викладачів"
                else:
                    # Якщо викладачі не вибрані, але вибрані кафедри
                    selected_departments = context.user_data.get("selected_departments", [])
                    if selected_departments:
                        # Отримуємо chat_id для всіх викладачів вказаних кафедр
                        chat_ids = get_chat_ids_by_departments(db, selected_departments)
                        teacher_stats = f"всі викладачі {len(selected_departments)} кафедр"

        # Відправляємо оголошення всім вибраним користувачам
        chat_ids = [chat_id[0] for chat_id in chat_ids]  # Розпакування ChatID

        for chat_id in chat_ids:
            if chat_id:
                try:
                    # Перевіряємо наявність різних типів контенту
                    if update.message.text:
                        print(f"📢 Відправляю текстове оголошення до {chat_id}")
                        await context.bot.send_message(
                            chat_id=chat_id,
                            text=f"📢 ОГОЛОШЕННЯ:\n\n{update.message.text}"
                        )
                        recipients_count += 1

                        if update.message.photo:
                            # Перевірка, чи є фото
                            photo = update.message.photo[-1]  # Беремо найбільшу версію фото
                            if photo.file_id:
                                print(f"📷 Відправляю фото до {chat_id}, file_id: {photo.file_id}")
                                await context.bot.send_photo(
                                    chat_id=chat_id,
                                    photo=photo.file_id,
                                    caption=f"📢 ОГОЛОШЕННЯ:\n\n{update.message.caption or announcement_text}"
                                )
                                recipients_count += 1

                        if update.message.video:
                            # Перевірка наявності відео
                            video = update.message.video
                            if video and video.file_id:
                                print(f"🎥 Відправляю відео до {chat_id}, file_id: {video.file_id}")
                                await context.bot.send_video(
                                    chat_id=chat_id,
                                    video=video.file_id,
                                    caption=f"📢 ОГОЛОШЕННЯ:\n\n{update.message.caption or announcement_text}"
                                )
                                recipients_count += 1

                        if update.message.document:
                            # Перевірка наявності документу
                            document = update.message.document
                            if document and document.file_id:
                                print(f"📄 Відправляю документ до {chat_id}, file_id: {document.file_id}")
                                await context.bot.send_document(
                                    chat_id=chat_id,
                                    document=document.file_id,
                                    caption=f"📢 ОГОЛОШЕННЯ:\n\n{update.message.caption or announcement_text}"
                                )
                                recipients_count += 1


                except Exception as e:
                            logger.error(f"❌ Помилка відправки повідомлення до chat_id {chat_id}: {e}")
                            print(f"❌ Помилка надсилання: {e}")


        # Формуємо повідомлення з результатами розсилки
        if recipients_count > 0:
            summary_message = "✅ Оголошення успішно відправлено!\n\n"
            summary_message += f"Категорія: {'Студенти' if announcement_to == 'students' else 'Викладачі'}\n"

            if announcement_to == "students":
                selected_groups = context.user_data.get("selected_groups", [])
                selected_courses = context.user_data.get("selected_courses", [])

                if selected_groups:
                    summary_message += f"Охоплено {len(selected_groups)} груп\n"
                elif selected_courses:
                    summary_message += f"Охоплено студентів {len(selected_courses)} курсів\n"
            else:
                selected_teachers = context.user_data.get("selected_teachers", [])
                selected_departments = context.user_data.get("selected_departments", [])

                if selected_teachers:
                    summary_message += f"Охоплено {len(selected_teachers)} викладачів\n"
                elif selected_departments:
                    summary_message += f"Охоплено викладачів {len(selected_departments)} кафедр\n"

            summary_message += f"Успішно доставлено: {recipients_count} користувачам\n"
            summary_message += f"\nТекст оголошення:\n\n{announcement_text}"
            await update.message.reply_text(summary_message)
        else:
            await update.message.reply_text(
                "❌ Не вдалося надіслати оголошення. Можливі причини:\n"
                "- Немає отримувачів з Telegram ID в базі\n"
                "- Не вибрано жодного отримувача\n"
                "Переконайтеся, що ви правильно обрали отримувачів."
            )

    except Exception as e:
        logger.exception(f"Помилка при відправці оголошення: {e}")
        await update.message.reply_text(
            f"❌ Сталася помилка при відправці оголошення: {str(e)}\n"
            "Будь ласка, спробуйте пізніше або зверніться до адміністратора."
        )
    finally:
        # Очищаємо дані після відправки
        context.user_data.pop("state", None)
        context.user_data.pop("announcement_to", None)
        context.user_data.pop("selected_courses", None)
        context.user_data.pop("selected_groups", None)
        context.user_data.pop("selected_departments", None)
        context.user_data.pop("selected_teachers", None)