from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from source.announcements.publication import announcement_selector_handler
from source.auth.registration import start
from source.config import BOT_TOKEN
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
    application.add_handler(CallbackQueryHandler(announcement_selector_handler, pattern="^(announce_to_|course_|dept_|group_|teacher_|show_|confirm_|back_to_|cancel_)"))

    # Запуск бота
    application.run_polling()

if __name__ == "__main__":
    main()