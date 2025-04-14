
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, ConversationHandler, CommandHandler, CallbackQueryHandler
from sqlalchemy import select
from datetime import datetime

from source.config import WAITING_FOR_SCAN_LINK
from source.database import SessionLocal
from source.models import User, Student, DocumentType, DocumentRequest

SELECT_DOCUMENT, CONFIRM_REQUEST = range(2)

async def doc_request(update: Update, context: CallbackContext):
    """Ініціює процес замовлення документу."""
    # Перевіряємо, чи є користувач студентом
    with SessionLocal() as db:
        # Знаходимо користувача за ChatID
        db_user = db.query(User).filter(User.ChatID == update.effective_chat.id).first()

        if not db_user or db_user.Role != 'student':
            await update.message.reply_text("Замовлення документів доступне тільки для студентів.")
            return

        # Отримуємо запис студента
        student = db.query(Student).filter(Student.UserID == db_user.UserID).first()

        if not student:
            await update.message.reply_text("Не вдалося знайти дані студента. Зверніться до деканату.")
            return

        # Отримуємо список доступних типів документів
        document_types = db.query(DocumentType).all()

        if not document_types:
            await update.message.reply_text("На даний момент немає доступних типів документів для замовлення.")
            return

        # Створюємо інлайн клавіатуру з типами документів
        keyboard = []
        for doc_type in document_types:
            keyboard.append([InlineKeyboardButton(doc_type.TypeName, callback_data=f"doc_select_{doc_type.TypeID}")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "Оберіть тип документа, який бажаєте замовити:",
            reply_markup=reply_markup
        )

async def select_document(update: Update, context: CallbackContext):
    """Обробляє вибір типу документу."""
    query = update.callback_query
    await query.answer()

    # Отримуємо ID типу документа з callback_data
    document_type_id = int(query.data.split('_')[2])

    # Зберігаємо ID студента
    with SessionLocal() as db:
        db_user = db.query(User).filter(User.ChatID == update.effective_chat.id).first()
        student = db.query(Student).filter(Student.UserID == db_user.UserID).first()

        document_type = db.query(DocumentType).filter(DocumentType.TypeID == document_type_id).first()

        if not document_type:
            await query.edit_message_text("Помилка: обраний тип документа не знайдено.")
            return

        # Створюємо кнопки для підтвердження або скасування
        keyboard = [
            [InlineKeyboardButton("Підтвердити", callback_data=f"doc_confirm_{document_type_id}_{student.StudentID}")],
            [InlineKeyboardButton("Скасувати", callback_data="cancel_doc")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"Ви обрали: {document_type.TypeName}\n\nБажаєте підтвердити замовлення?",
            reply_markup=reply_markup
        )

async def cancel_document_request(update: Update, context: CallbackContext):
    """Скасовує замовлення документа."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Замовлення документа скасовано.")



async def doc_requested(update: Update, context: CallbackContext):
    with SessionLocal() as db:
        pending_requests = db.query(DocumentRequest).filter(DocumentRequest.Status == 'pending').all()

        if not pending_requests:
            await update.message.reply_text("Немає заявок на документи для опрацювання.")
            return

        message = "📄 Список заявок:\n\n"
        keyboard = []

        for req in pending_requests:
            student = db.query(Student).filter(Student.StudentID == req.StudentID).first()
            user = db.query(User).filter(User.UserID == student.UserID).first()
            doc_type = db.query(DocumentType).filter(DocumentType.TypeID == req.TypeID).first()

            message += f"№ {req.RequestID}: {doc_type.TypeName}, Студент: {user.UserName}\n"
            keyboard.append([InlineKeyboardButton(f"Обрати №{req.RequestID}", callback_data=f"handle_request_{req.RequestID}")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(message, reply_markup=reply_markup)

async def handle_doc_request(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    request_id = int(query.data.split('_')[2])

    keyboard = [
        [InlineKeyboardButton("✅ Опрацювати", callback_data=f"process_doc_{request_id}")],
        [InlineKeyboardButton("❌ Відхилити", callback_data=f"reject_doc_{request_id}")]
    ]

    await query.edit_message_text(
        f"Заявка №{request_id}: Оберіть дію:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def reject_document_request(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    request_id = int(query.data.split('_')[2])

    with SessionLocal() as db:
        request = db.query(DocumentRequest).filter(DocumentRequest.RequestID == request_id).first()
        request.Status = 'rejected'
        db.commit()

        student = db.query(Student).filter(Student.StudentID == request.StudentID).first()
        user = db.query(User).filter(User.UserID == student.UserID).first()

        await context.bot.send_message(
            chat_id=user.ChatID,
            text=f"❌ Ваша заявка №{request.RequestID} на документ була відхилена."
        )

    await query.edit_message_text(f"Заявка №{request_id} була відхилена.")

async def process_document_request(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    request_id = int(query.data.split('_')[2])

    context.user_data["processing_request_id"] = request_id
    context.user_data["state"] = WAITING_FOR_SCAN_LINK
    await query.edit_message_text("Введіть посилання на скан документу:")

