from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from source.announcements.publication import announcement_selector_handler
from source.auth.registration import start, confirm_callback_handler, confirm_command, confirm, delete_user_handler, \
    get_groups_list, edit_user_handler, register_edit_handlers, edit_field_handler
from source.config import BOT_TOKEN
from source.courses.handlers import course_callback_handler, back_to_courses_handler
from source.documents.db_queries import confirm_document_request
from source.documents.handlers import doc_request, select_document, cancel_document_request, handle_doc_request, \
    reject_document_request, process_document_request
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

    # Важливо: спочатку реєструємо обробники з точнішими шаблонами
    application.add_handler(CallbackQueryHandler(edit_field_handler, pattern=r"^edit_[a-z]+_\w+$"))
    application.add_handler(CallbackQueryHandler(edit_user_handler, pattern=r"^edit_\w+$"))

    # Обробник підтвердження реєстрації
    application.add_handler(CallbackQueryHandler(confirm_callback_handler, pattern=r"^confirm_|cancel_"))

    # Обробник видалення заявки
    application.add_handler(CallbackQueryHandler(delete_user_handler, pattern=r"^delete_"))

    # Загальні обробники оголошень
    application.add_handler(CallbackQueryHandler(announcement_selector_handler, pattern="^(announce_to_|course_|dept_|group_|teacher_|show_|back_to_|cancel_)"))

    # Реєстрація обробників команд
    application.add_handler(CommandHandler("confirm", confirm_command))
    application.add_handler(CommandHandler("groups", get_groups_list))
    application.add_handler(MessageHandler(filters.Regex("^Підтвердити реєстрацію$"), confirm))
    application.add_handler(CallbackQueryHandler(back_to_courses_handler, pattern="^back_teachercourses$"))
    application.add_handler(CallbackQueryHandler(course_callback_handler, pattern="^teachercourse_"))

    application.add_handler(CommandHandler('doc_request', doc_request))
    application.add_handler(CallbackQueryHandler(select_document, pattern='^doc_select_'))
    application.add_handler(CallbackQueryHandler(confirm_document_request, pattern='^doc_confirm_'))
    application.add_handler(CallbackQueryHandler(cancel_document_request, pattern='^cancel_doc$'))

    application.add_handler(CallbackQueryHandler(handle_doc_request, pattern="^handle_request_"))
    application.add_handler(CallbackQueryHandler(reject_document_request, pattern="^reject_doc_"))
    application.add_handler(CallbackQueryHandler(process_document_request, pattern="^process_doc_"))

    # Запуск бота
    application.run_polling()

if __name__ == "__main__":
    main()