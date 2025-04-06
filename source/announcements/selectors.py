from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup

import datetime as dt
import logging
from telegram import Update
from telegram.ext import CallbackContext



logger = logging.getLogger(__name__)
from source.database import SessionLocal
from source.db_queries import get_groups_by_admission_years, get_teachers_by_departments, get_all_departments


# Функція для вибору курсу студентів
async def show_student_course_selector(update: Update, context: CallbackContext):
    """Показує кнопки вибору курсу студентів."""
    query = update.callback_query

    # Створюємо кнопки для вибору курсу (з 1 по 6)
    keyboard = []
    selected_courses = context.user_data.get("selected_courses", [])

    # Створюємо рядки по 3 курси в рядку
    for i in range(1, 7, 3):
        row = []
        for j in range(i, min(i+3, 7)):
            # Додаємо символ ✓, якщо курс вибраний
            checkbox = "✓ " if j in selected_courses else ""
            row.append(InlineKeyboardButton(
                f"{checkbox}{j} курс",
                callback_data=f"course_{j}"
            ))
        keyboard.append(row)

    # Додаємо додаткові кнопки
    bottom_row = []
    if selected_courses:
        bottom_row.append(InlineKeyboardButton("Вибрати групи", callback_data="show_groups"))
        bottom_row.append(InlineKeyboardButton("Підтвердити всі курси", callback_data="confirm_student_selection"))

    if bottom_row:
        keyboard.append(bottom_row)

    # Додаємо кнопку скасування
    keyboard.append([InlineKeyboardButton("Скасувати", callback_data="cancel_announcement")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        "Виберіть курс(и) для оголошення:\n"
        "(Ви можете вибрати кілька курсів)",
        reply_markup=reply_markup
    )

# Функція для оновлення селектора курсів
async def update_course_selector(update: Update, context: CallbackContext):
    """Оновлює кнопки вибору курсу студентів."""
    await show_student_course_selector(update, context)

# Функція для вибору груп
async def show_group_selector(update: Update, context: CallbackContext):
    """Показує кнопки вибору груп для вибраних курсів."""
    query = update.callback_query

    try:
        selected_courses = context.user_data.get("selected_courses", [])

        if not selected_courses:
            await query.edit_message_text("Спочатку виберіть хоча б один курс.")
            return

        # Отримуємо поточний рік для обчислення року вступу
        current_year = dt.datetime.now().year

        # Обчислюємо роки вступу для вибраних курсів
        admission_years = [current_year - course + 1 for course in selected_courses]

        # Отримуємо групи для вибраних курсів з бази даних
        with SessionLocal() as db:
            groups = get_groups_by_admission_years(db, admission_years)

            if not groups:
                await query.edit_message_text(
                    "Не знайдено груп для вибраних курсів. Поверніться назад і виберіть інші курси.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("Назад до вибору курсів", callback_data="back_to_courses")
                    ]])
                )
                return

            # Створюємо кнопки для груп
            keyboard = []
            selected_groups = context.user_data.get("selected_groups", [])

            # Групуємо групи по курсах для зручності
            groups_by_course = {}
            for group_id, group_name, admission_year in groups:
                course = current_year - admission_year + 1
                if course not in groups_by_course:
                    groups_by_course[course] = []
                groups_by_course[course].append((group_id, group_name))

            # Створюємо кнопки для кожної групи, організовані по курсах
            for course in sorted(groups_by_course.keys()):
                keyboard.append([InlineKeyboardButton(f"--- {course} курс ---", callback_data="course_header")])

                # Створюємо рядки з групами, по 2 групи в рядку
                course_groups = groups_by_course[course]
                for i in range(0, len(course_groups), 2):
                    row = []
                    for j in range(i, min(i+2, len(course_groups))):
                        group_id, group_name = course_groups[j]
                        # Додаємо символ ✓, якщо група вибрана
                        checkbox = "✓ " if group_id in selected_groups else ""
                        row.append(InlineKeyboardButton(
                            f"{checkbox}{group_name}",
                            callback_data=f"group_{group_id}"
                        ))
                    keyboard.append(row)

            # Додаємо кнопки навігації та підтвердження
            nav_row = [
                InlineKeyboardButton("Назад до курсів", callback_data="back_to_courses")
            ]

            if selected_groups or selected_courses:
                nav_row.append(InlineKeyboardButton("Підтвердити вибір", callback_data="confirm_student_selection"))

            keyboard.append(nav_row)
            keyboard.append([InlineKeyboardButton("Скасувати", callback_data="cancel_announcement")])

            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "Виберіть групи для оголошення:\n"
                "(Ви можете вибрати кілька груп або всі групи обраних курсів)",
                reply_markup=reply_markup
            )
    except Exception as e:
        logger.exception(f"Помилка при відображенні селектора груп: {e}")
        await query.edit_message_text(
            f"Помилка при завантаженні груп. Спробуйте пізніше.\nПомилка: {str(e)}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Назад", callback_data="back_to_courses")
            ]])
        )

# Функція для оновлення селектора груп
async def update_group_selector(update: Update, context: CallbackContext):
    """Оновлює кнопки вибору груп."""
    await show_group_selector(update, context)

# Функція для вибору кафедр
async def show_department_selector(update: Update, context: CallbackContext):
    """Показує кнопки вибору кафедр."""
    query = update.callback_query

    try:
        # Отримуємо кафедри з бази даних
        with SessionLocal() as db:
            departments = get_all_departments(db)

            if not departments:
                await query.edit_message_text(
                    "Не знайдено кафедр у базі даних.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("Скасувати", callback_data="cancel_announcement")
                    ]])
                )
                return

            # Створюємо кнопки для кафедр
            keyboard = []
            selected_departments = context.user_data.get("selected_departments", [])

            # Створюємо рядки з кафедрами, по 1 кафедрі в рядку
            for dept_id, dept_name in departments:
                # Додаємо символ ✓, якщо кафедра вибрана
                checkbox = "✓ " if dept_id in selected_departments else ""
                keyboard.append([
                    InlineKeyboardButton(
                        f"{checkbox}{dept_name}",
                        callback_data=f"dept_{dept_id}"
                    )
                ])

            # Додаємо кнопки навігації та підтвердження
            nav_row = []

            if selected_departments:
                nav_row.append(InlineKeyboardButton("Вибрати викладачів", callback_data="show_teachers"))
                nav_row.append(InlineKeyboardButton("Підтвердити всі кафедри", callback_data="confirm_teacher_selection"))

            if nav_row:
                keyboard.append(nav_row)

            keyboard.append([InlineKeyboardButton("Скасувати", callback_data="cancel_announcement")])

            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "Виберіть кафедри для оголошення:\n"
                "(Ви можете вибрати кілька кафедр)",
                reply_markup=reply_markup
            )
    except Exception as e:
        logger.exception(f"Помилка при відображенні селектора кафедр: {e}")
        await query.edit_message_text(
            f"Помилка при завантаженні кафедр. Спробуйте пізніше.\nПомилка: {str(e)}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Скасувати", callback_data="cancel_announcement")
            ]])
        )

# Функція для оновлення селектора кафедр
async def update_department_selector(update: Update, context: CallbackContext):
    """Оновлює кнопки вибору кафедр."""
    await show_department_selector(update, context)

# Функція для вибору викладачів
async def show_teacher_selector(update: Update, context: CallbackContext):
    """Показує кнопки вибору викладачів для вибраних кафедр."""
    query = update.callback_query

    try:
        selected_departments = context.user_data.get("selected_departments", [])

        if not selected_departments:
            await query.edit_message_text("Спочатку виберіть хоча б одну кафедру.")
            return

        # Отримуємо викладачів для вибраних кафедр з бази даних
        with SessionLocal() as db:
            teachers = get_teachers_by_departments(db, selected_departments)

            if not teachers:
                await query.edit_message_text(
                    "Не знайдено викладачів для вибраних кафедр. Поверніться назад і виберіть інші кафедри.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("Назад до вибору кафедр", callback_data="back_to_departments")
                    ]])
                )
                return

            # Створюємо кнопки для викладачів
            keyboard = []
            selected_teachers = context.user_data.get("selected_teachers", [])

            # Групуємо викладачів по кафедрах для зручності
            teachers_by_dept = {}
            for teacher_id, teacher_name, dept_id, dept_name in teachers:
                if dept_id not in teachers_by_dept:
                    teachers_by_dept[dept_id] = {"name": dept_name, "teachers": []}
                teachers_by_dept[dept_id]["teachers"].append((teacher_id, teacher_name))

            # Створюємо кнопки для кожного викладача, організовані по кафедрах
            for dept_id in sorted(teachers_by_dept.keys()):
                dept_info = teachers_by_dept[dept_id]
                keyboard.append([InlineKeyboardButton(f"--- {dept_info['name']} ---", callback_data="dept_header")])

                # Створюємо рядки з викладачами, по 1 викладачу в рядку
                for teacher_id, teacher_name in dept_info["teachers"]:
                    # Додаємо символ ✓, якщо викладач вибраний
                    checkbox = "✓ " if teacher_id in selected_teachers else ""
                    keyboard.append([
                        InlineKeyboardButton(
                            f"{checkbox}{teacher_name}",
                            callback_data=f"teacher_{teacher_id}"
                        )
                    ])

            # Додаємо кнопки навігації та підтвердження
            nav_row = [
                InlineKeyboardButton("Назад до кафедр", callback_data="back_to_departments")
            ]

            if selected_teachers or selected_departments:
                nav_row.append(InlineKeyboardButton("Підтвердити вибір", callback_data="confirm_teacher_selection"))

            keyboard.append(nav_row)
            keyboard.append([InlineKeyboardButton("Скасувати", callback_data="cancel_announcement")])

            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "Виберіть викладачів для оголошення:\n"
                "(Ви можете вибрати кількох викладачів або всі кафедри)",
                reply_markup=reply_markup
            )
    except Exception as e:
        logger.exception(f"Помилка при відображенні селектора викладачів: {e}")
        await query.edit_message_text(
            f"Помилка при завантаженні викладачів. Спробуйте пізніше.\nПомилка: {str(e)}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Назад", callback_data="back_to_departments")
            ]])
        )

# Функція для оновлення селектора викладачів
async def update_teacher_selector(update: Update, context: CallbackContext):
    """Оновлює кнопки вибору викладачів."""
    await show_teacher_selector(update, context)
