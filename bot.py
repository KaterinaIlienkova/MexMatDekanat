from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from source.announcements.publication import announcement_selector_handler
from source.auth.registration import start, confirm_callback_handler, confirm_command, confirm
from source.config import BOT_TOKEN
from source.courses.handlers import course_callback_handler, back_to_courses_handler
from source.faq.handlers import register_faq_handlers
from source.utils import message_handler


def main():
    # Створюємо об'єкт додатку
    application = Application.builder().token(BOT_TOKEN).build()

    # Додаємо обробники команд
    application.add_handler(CommandHandler("start", start))

    # Обробник повідомлень
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    register_faq_handlers(application)

    # Спочатку реєструємо більш специфічний обробник для підтвердження
    application.add_handler(CallbackQueryHandler(confirm_callback_handler, pattern=r"^confirm_|cancel_confirmation$"))

    # Потім реєструємо загальний обробник для оголошень
    application.add_handler(CallbackQueryHandler(announcement_selector_handler, pattern="^(announce_to_|course_|dept_|group_|teacher_|show_|back_to_|cancel_)"))

    # Реєстрація обробників команд
    application.add_handler(CommandHandler("confirm", confirm_command))
    application.add_handler(MessageHandler(filters.Regex("^Підтвердити реєстрацію$"), confirm))
    application.add_handler(CallbackQueryHandler(back_to_courses_handler, pattern="^back_teachercourses$"))
    application.add_handler(CallbackQueryHandler(course_callback_handler, pattern="^teachercourse_"))

    # Запуск бота
    application.run_polling()

if __name__ == "__main__":
    main()